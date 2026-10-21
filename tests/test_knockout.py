import io
import json
import threading
import time
import zipfile

import pytest
from fastapi.testclient import TestClient

from arena import competition, knockout
from arena.runner import Match
from arena.sdk import RULES_VERSION


def config(roster, **changes):
    return {"kind":"knockout", "roster":roster, "games_per_pair":8, "seed":42,
            "mode":"elimination", "name":"Finals", "shuffle":False, **changes}


def add_games(rows, node, cfg, count, winner):
    for _ in range(count):
        rows.append({**knockout.next_fixture(cfg, {**node,"played":node["played"]+_}),"winner":winner})


def test_seed_order_byes_and_reproducible_shuffle():
    for count in range(2,17):
        roster=[str(i) for i in range(count)]
        report=knockout.bracket_report(config(roster),[])
        opening=report["rounds"][0]["series"]
        assert sorted(p for n in opening for p in n["participants"] if p is not None)==sorted(roster)
        assert all(any(p is not None for p in n["participants"]) for n in opening)
        assert sum(n["status"]=="bye" for n in opening)==len(opening)*2-count
        assert report["expected_games"]==(count-1)*8
        assert len(report["series"])==len(opening)*2-1
    assert knockout.seed_order(8)==[0,7,3,4,1,6,2,5]
    cfg=config(list('abcdefgh'),shuffle=True)
    assert knockout.bracket_report(cfg,[])["seeded_roster"]==knockout.bracket_report(cfg,[])["seeded_roster"]
    assert knockout.bracket_report(cfg,[])["seeded_roster"]!=cfg["roster"]


def test_semifinals_feed_final_and_final_winner_not_cumulative_points():
    cfg=config(list('abcd')); rows=[]
    report=knockout.bracket_report(cfg,rows)
    assert report['series'][-1]['participants']==[None,None]
    for sid,winner in [('r1s1','a'),('r1s2','b'),('r2s1','b')]:
        node=next(n for n in knockout.bracket_report(cfg,rows)['series'] if n['id']==sid)
        assert node['status']=='ready'
        add_games(rows,node,cfg,8,winner)
    report=knockout.bracket_report(cfg,rows)
    assert report['winner']=='b' and report['leaders']==['b']
    assert report['series'][-1]['participants']==['a','b']
    assert report['games']==report['expected_games']==24
    assert len({row['index'] for row in rows})==24


def test_ties_use_full_balanced_blocks_then_require_recorded_ruling():
    cfg=config(['a','b']); rows=[]
    for target in (16,24,24):
        node=knockout.bracket_report(cfg,rows)['series'][0]
        add_games(rows,node,cfg,8,None)
        report=knockout.bracket_report(cfg,rows)
        assert report['series'][0]['target']==target
        assert not report['winner']
    assert report['series'][0]['status']=='awaiting_decision'
    ruling={'series_id':'r1s1','winner':'b','reason':'Announced organizer ruling','created_at':1}
    report=knockout.bracket_report(cfg,rows,[ruling])
    assert report['winner']=='b' and report['series'][0]['ruling']==ruling


def test_tiebreak_can_resolve_without_ruling_and_preserves_seat_balance():
    cfg=config(['a','b']); rows=[]
    add_games(rows,knockout.bracket_report(cfg,rows)['series'][0],cfg,8,None)
    node=knockout.bracket_report(cfg,rows)['series'][0]
    add_games(rows,node,cfg,8,'a')
    report=knockout.bracket_report(cfg,rows)
    assert report['winner']=='a' and report['expected_games']==16
    for block in (rows[:8],rows[8:]):
        assert {(r['bots'].index('a'),r['rotation']) for r in block}=={(s,r) for s in range(2) for r in range(4)}
    assert rows[0]['seed']!=rows[8]['seed']


def quick_matches(monkeypatch,stop=None):
    def make(ids,registry,**kwargs):
        match=Match(ids,registry,max_ticks=2,**kwargs)
        if stop:
            original=match.run
            def run():
                result=original();stop.set();return result
            match.run=run
        return match
    monkeypatch.setattr(competition,'Match',make)


def test_knockout_checkpoint_resume_tie_and_runtime_guard(tmp_path,monkeypatch):
    stop=threading.Event();quick_matches(monkeypatch,stop)
    cfg=config(['random','hunter'])
    job={'id':'b'*32,'config':cfg,'rows':[],'decisions':[],'status':'running',
         'entries':competition.snapshot_entries(cfg['roster'],{},tmp_path/'entries'),
         'runtime_digest':competition.runtime_digest(),'rules_version':RULES_VERSION}
    knockout.run_knockout(job,tmp_path,stop)
    assert job['status']=='paused' and job['completed']==1
    saved=json.loads((tmp_path/'evaluations'/(job['id']+'.json')).read_text())
    first=saved['rows'][0].copy();stop.clear();quick_matches(monkeypatch)
    saved['status']='running';knockout.run_knockout(saved,tmp_path,stop)
    assert saved['status']=='awaiting_decision' and saved['completed']==24
    assert saved['rows'][0]==first and len({r['index'] for r in saved['rows']})==24
    saved['decisions']=[{'series_id':'r1s1','winner':'hunter','reason':'Published policy applied'}]
    saved['status']='running';knockout.run_knockout(saved,tmp_path)
    assert saved['status']=='complete' and saved['report']['winner']=='hunter'
    assert len(list((tmp_path/'replays').glob('*.json')))==24
    saved['runtime_digest']='changed';knockout.run_knockout(saved,tmp_path)
    assert saved['status']=='failed' and 'runtime' in saved['error']


def test_knockout_api_tied_series_rulings_recovery_and_release(tmp_path,monkeypatch):
    from arena import server
    for folder in ('bots','replays','evaluations'):(tmp_path/folder).mkdir()
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(server,'jobs',{})
    monkeypatch.setattr(server,'tasks',set())
    monkeypatch.setattr(server,'competition_stops',{})
    quick_matches(monkeypatch)
    def settled(client,jid):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            job=client.get('/api/evaluations/'+jid).json()
            if job['status']!='running':return job
            time.sleep(.01)
        pytest.fail('Tournament did not settle')
    with TestClient(server.app) as client:
        assert client.post('/api/knockouts',json={'roster':['random','random']}).status_code==400
        job=client.post('/api/knockouts',json={'roster':['random','hunter','survivor'],'shuffle':False}).json();jid=job['id']
        job=settled(client,jid)
        assert job['status']=='awaiting_decision'
        assert job['report']['series'][0]['status']=='bye'
        assert client.get('/api/evaluations').json()[0]['config']['kind']=='knockout'
        assert client.post('/api/knockouts/'+jid+'/resume').status_code==409
        assert client.get('/api/knockouts/'+jid+'/release').status_code==409
        path='/api/knockouts/'+jid+'/decision'
        assert client.post(path,json={'series_id':'r1s2','winner':'random','reason':'Invalid participant'}).status_code==400
        assert client.post(path,json={'series_id':'r1s2','winner':'hunter','reason':'     '}).status_code==400
        # Waiting ties survive a process reload; no unsaved implicit winner.
        server.jobs.clear()
        assert client.get('/api/evaluations/'+jid).json()['status']=='awaiting_decision'
        for sid,winner in [('r1s2','hunter'),('r2s1','random')]:
            response=client.post(path,json={'series_id':sid,'winner':winner,'reason':'Published tie policy applied'})
            assert response.status_code==200,response.text
            job=settled(client,jid)
        assert job['status']=='complete' and job['report']['winner']=='random'
        assert job['completed']==job['total']==48 and len(job['decisions'])==2
        assert len({r['index'] for r in job['rows']})==48
        assert client.post(path,json={'series_id':'r2s1','winner':'hunter','reason':'Cannot change completed result'}).status_code==409
        release=client.get('/api/knockouts/'+jid+'/release')
        assert release.status_code==200
        with zipfile.ZipFile(io.BytesIO(release.content)) as archive:
            assert len([p for p in archive.namelist() if p.startswith('replays/')])==48
            content=''.join(archive.read(p).decode() for p in archive.namelist())
            assert 'Published tie policy applied' not in content and jid not in content
            assert 'r1s2' not in content and 'r2s1' not in content
