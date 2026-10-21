import copy
import json
import threading
import time
import zipfile
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from arena import competition
from arena.engine import Game
from arena.runner import Match
from arena.sdk import RULES_VERSION


def job_for(roster, data):
    return {"id":"a"*32,"config":{"kind":"round_robin","roster":roster,"games_per_pair":8,"seed":42,"mode":"elimination","name":"Class"},
            "status":"running","rows":[],"completed":0,"total":len(roster)*(len(roster)-1)//2*8,
            "entries":competition.snapshot_entries(roster,{},data/'entries'),"runtime_digest":competition.runtime_digest(),
            "rules_version":RULES_VERSION,"created_at":1}


def quick_matches(monkeypatch, stop=None):
    def make(ids,registry,**kwargs):
        match=Match(ids,registry,max_ticks=2,**kwargs)
        if stop:
            original=match.run
            def run():
                result=original();stop.set();return result
            match.run=run
        return match
    monkeypatch.setattr(competition,'Match',make)


def test_schedule_covers_every_pair_seat_corner_and_shared_map():
    roster=['random','hunter','survivor','bomber']
    schedule=list(competition.fixtures(roster,16,123))
    assert len(schedule)==6*16
    assert len({f['index'] for f in schedule})==len(schedule)
    assert set(Counter(tuple(f['participants']) for f in schedule).values())=={16}
    for a,b in combinations(roster,2):
        games=[f for f in schedule if f['participants']==[a,b]]
        assert len(games)==16
        assert {(g['bots'].index(a),g['rotation']) for g in games}=={(s,r) for s in range(2) for r in range(4)}
    for game in range(16):
        assert {f['seed'] for f in schedule if f['game_in_pair']==game}=={123+game//8}
    assert schedule==list(competition.fixtures(roster,16,123))


def test_standings_points_and_shared_ranks(tmp_path):
    players=Game(['a','b']).snapshot()['players']
    rows=[{'participants':['a','b'],'bots':['a','b'],'winner':None,'players':players,'errors':{}},
          {'participants':['a','c'],'bots':['c','a'],'winner':'a','players':players,'errors':{}},
          {'participants':['b','c'],'bots':['b','c'],'winner':'b','players':players,'errors':{}}]
    report=competition.summarize(['a','b','c'],rows)
    table={s['bot']:s for s in report['standings']}
    assert table['a']['points']==table['b']['points']==4
    assert table['a']['rank']==table['b']['rank']==1 and table['c']['rank']==3
    assert report['winner'] is None and report['leaders']==['a','b']
    assert table['a']['wins']==1 and table['a']['draws']==1


def test_snapshots_preserve_models_and_detect_mutation(tmp_path):
    source=tmp_path/'source';source.mkdir()
    (source/'bot.py').write_text('class Bot: pass')
    (source/'model.json').write_text('{"setting":2}')
    entries=competition.snapshot_entries(['student'],{'student':{'name':'Secret team','path':str(source/'bot.py')}},tmp_path/'frozen')
    frozen=Path(entries['student']['path'])
    assert frozen.with_name('model.json').read_text()=='{"setting":2}'
    (source/'model.json').write_text('{"setting":3}')
    competition.verify_entries(entries)
    frozen.with_name('model.json').write_text('{"setting":4}')
    with pytest.raises(ValueError,match='frozen submission changed'):
        competition.verify_entries(entries)
    assert 'path' not in competition.public_job({'entries':entries})['entries']['student']


def test_pause_resume_and_atomic_completed_match_recovery(tmp_path,monkeypatch):
    stop=threading.Event()
    quick_matches(monkeypatch,stop)
    job=job_for(['random','hunter','survivor'],tmp_path)
    competition.run_round_robin(job,tmp_path,stop)
    assert job['status']=='paused' and job['completed']==1
    saved=json.loads((tmp_path/'evaluations'/(job['id']+'.json')).read_text())
    first=copy.deepcopy(saved['rows'][0])
    assert all(p['name'] in ('Player 1','Player 2') for p in first['players'])
    stop.clear();quick_matches(monkeypatch)
    saved['status']='running'
    competition.run_round_robin(saved,tmp_path,stop)
    assert saved['status']=='complete' and saved['completed']==24
    assert saved['rows'][0]==first and len({r['index'] for r in saved['rows']})==24
    assert len(list((tmp_path/'replays').glob('*.json')))==24
    assert all(s['played']==16 and s['draws']==16 for s in saved['report']['standings'])
    assert not list((tmp_path/'evaluations').glob('.pending-*'))


def test_runtime_change_prevents_mixed_rule_resume(tmp_path):
    job=job_for(['random','hunter'],tmp_path);job['runtime_digest']='changed'
    competition.run_round_robin(job,tmp_path)
    assert job['status']=='failed' and not job['rows']
    assert 'runtime' in job['error']


def test_custom_bot_model_and_scratch_state_reset_each_match(tmp_path,monkeypatch):
    quick_matches(monkeypatch)
    source=tmp_path/'submission';source.mkdir()
    (source/'bot.py').write_text('''import json
from pathlib import Path
class Bot:
 def __init__(self):
  self.reused=Path("scratch.txt").exists()
  Path("scratch.txt").write_text("temporary")
  self.setting=json.loads(Path(__file__).with_name("model.json").read_text())["setting"]
 def choose_action(self,obs):
  return "wait" if not self.reused and self.setting==2 and obs["self"]["name"].startswith("Player ") else "invalid"
''')
    (source/'model.json').write_text('{"setting":2}')
    job=job_for(['random','hunter'],tmp_path)
    job['config']['roster']=['random','student']
    job['entries']=competition.snapshot_entries(['random','student'],{'student':{'name':'Private team','path':str(source/'bot.py')}},tmp_path/'entries')
    competition.run_round_robin(job,tmp_path)
    assert job['status']=='complete',job.get('error')
    assert all(not row['errors'] and all(p['invalid_actions']==0 for p in row['players']) for row in job['rows'])
    assert not list((tmp_path/'competitions'/job['id']).glob('.match-*'))


def test_anonymous_replay_drops_nested_identity_text():
    m=Match(['random','hunter'],max_ticks=1);m.run();replay=m.replay()
    secret='SECRET_TEAM_OR_PATH_123'
    replay.update(bot_ids=[secret,secret],metadata={'team':secret},errors={'0':secret})
    for frame in replay['frames']:
        frame['private']=secret;frame['events']=[{'text':secret}]
        for p in frame['players']:p.update(name=secret,private={'path':secret})
        frame['bombs']=[{'x':3,'y':3,'owner':0,'explode_at':10,'private':secret}]
    clean=competition.anonymous_replay(replay)
    assert secret not in json.dumps(clean)
    assert clean['version']==1 and clean['bot_ids']==['player_1','player_2']
    assert len(clean['frames'])==len(replay['frames'])
    assert clean['frames'][-1]['players'][1]['name']=='Player 2'
    assert replay['errors']['0']==secret


def test_release_pack_has_all_matches_and_is_cached(tmp_path,monkeypatch):
    quick_matches(monkeypatch)
    job=job_for(['random','hunter'],tmp_path)
    competition.run_round_robin(job,tmp_path)
    path=competition.build_release(job,tmp_path)
    before=path.read_bytes()
    assert competition.build_release(job,tmp_path).read_bytes()==before
    with zipfile.ZipFile(path) as archive:
        files=[n for n in archive.namelist() if n.startswith('replays/')]
        assert len(files)==8
        results=json.loads(archive.read('results.json'))
        assert len(results['matches'])==8
        for file in files:
            text=archive.read(file).decode()
            assert 'random' not in text and 'hunter' not in text and job['id'] not in text
            assert json.loads(text)['frames'][0]['players'][0]['name']=='Player 1'


@pytest.fixture
def local_server(tmp_path,monkeypatch):
    import arena.server as server
    for folder in ('bots','replays','evaluations'): (tmp_path/folder).mkdir()
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(server,'jobs',{})
    monkeypatch.setattr(server,'tasks',set())
    monkeypatch.setattr(server,'competition_stops',{})
    return server


def test_round_robin_api_validates_and_runs_with_legacy_history(local_server,monkeypatch):
    quick_matches(monkeypatch)
    server=local_server
    monkeypatch.setattr(server,'registry',{f'entry_{i}':{'name':'Team','path':'unused'} for i in range(14)})
    with TestClient(server.app) as client:
        assert client.post('/api/round-robins',json={'roster':['random','random']}).status_code==400
        assert client.post('/api/round-robins',json={'roster':['random','missing']}).status_code==400
        assert client.post('/api/round-robins',json={'roster':['human','random']}).status_code==400
        assert client.post('/api/round-robins',json={'roster':['hunter','random'],'games_per_pair':12}).status_code==400
        assert client.post('/api/round-robins',json={'roster':['hunter']}).status_code==422
        assert client.post('/api/round-robins',json={'roster':['hunter','random']+list(server.registry),'games_per_pair':24}).status_code==400
        response=client.post('/api/round-robins',json={'roster':['hunter','random'],'name':'Week 1'})
        assert response.status_code==200
        jid=response.json()['id']
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            result=client.get('/api/evaluations/'+jid).json()
            if result['status']!='running':break
            time.sleep(.01)
        assert result['status']=='complete',result.get('error')
        assert result['completed']==result['total']==8
        assert client.get('/api/evaluations').json()[0]['config']['kind']=='round_robin'
        assert client.get('/api/replays/'+result['rows'][0]['replay_id']).status_code==200
        release=client.get('/api/round-robins/'+jid+'/release')
        assert release.status_code==200 and release.headers['content-type']=='application/zip'
        assert client.post('/api/round-robins/'+jid+'/resume').status_code==409
        assert client.get('/api/round-robins/missing/release').status_code==404


def test_api_recovery_and_shared_single_job_lock(local_server,monkeypatch):
    server=local_server
    monkeypatch.setattr(server,'launch_competition',lambda job:server.competition_stops.setdefault(job['id'],threading.Event()))
    with TestClient(server.app) as client:
        job=client.post('/api/round-robins',json={'roster':['hunter','random']}).json();jid=job['id']
        assert client.post('/api/evaluations',json={'candidate':'hunter'}).status_code==409
        assert client.get('/api/round-robins/'+jid+'/release').status_code==409
        assert client.post('/api/round-robins/'+jid+'/pause').json()['pause_requested']
        server.jobs.clear() # Simulate a new server process loading the last committed record.
        assert client.get('/api/evaluations/'+jid).json()['status']=='interrupted'
        assert client.get('/api/evaluations').json()[0]['status']=='interrupted'
        assert client.post('/api/round-robins/'+jid+'/resume').json()['status']=='running'
