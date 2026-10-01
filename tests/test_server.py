from fastapi.testclient import TestClient
from arena.server import app


def test_api_preview_and_validation():
    with TestClient(app) as client:
        assert len(client.get('/api/bots').json())>=4
        preview=client.get('/api/preview').json()
        assert len(preview['board'])==15 and len(preview['players'])==2
        assert client.post('/api/matches',json={'bots':['missing','hunter']}).status_code==400
        assert client.post('/api/matches',json={'bots':['human','human']}).status_code==400
        assert client.post('/api/matches',json={'bots':['hunter']}).status_code==422


def test_remote_origin_rejected():
    with TestClient(app) as client:
        r=client.post('/api/matches',json={'bots':['hunter','random']},headers={'Origin':'https://example.com'})
        assert r.status_code==403


def test_upload_requires_explicit_trust():
    with TestClient(app) as client:
        r=client.post('/api/bots/upload',data={'name':'test','trusted':'false'},files={'file':('bot.py',b'class Bot: pass')})
        assert r.status_code==400


def test_live_match_control_and_replay():
    with TestClient(app) as client:
        r=client.post('/api/matches',json={'bots':['random','hunter'],'seed':81})
        assert r.status_code==200
        mid=r.json()['id']
        assert client.post(f'/api/matches/{mid}/control',json={'paused':True}).status_code==200
        with client.websocket_connect(f'/ws/matches/{mid}') as ws:
            state=ws.receive_json()
            assert len(state['views'])==2
        client.post(f'/api/matches/{mid}/control',json={'step':True})
        assert client.get(f'/api/replays/{mid}').json()['frames'][-1]['tick']>=1
        client.post(f'/api/matches/{mid}/control',json={'stop':True})


def test_upload_validates_model_and_runs_bot(tmp_path,monkeypatch):
    import arena.server as server
    (tmp_path/'bots').mkdir()
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(server,'registry',{})
    code=b'class Bot:\n def choose_action(self, observation):\n  return "move_e"\n'
    with TestClient(app) as client:
        r=client.post('/api/bots/upload',data={'name':'Test contender','trusted':'true'},files={'file':('bot.py',code),'model':('model.json',b'{"test":true}')})
        assert r.status_code==200
        entry=r.json()
        assert entry['name']=='Test contender' and len(entry['version'])==8
        assert 'path' not in entry
        from arena.runner import Match
        match=Match([entry['id'],'random'],server.registry,max_ticks=1)
        match.run()
        assert match.game.players[0].x==2


def test_human_input_and_filtered_websocket():
    with TestClient(app) as client:
        mid=client.post('/api/matches',json={'bots':['human','hunter']}).json()['id']
        client.post(f'/api/matches/{mid}/control',json={'paused':True})
        before=client.get(f'/api/matches/{mid}').json()['players'][0]['x']
        client.post(f'/api/matches/{mid}/action',json={'action':'move_e'})
        client.post(f'/api/matches/{mid}/control',json={'step':True})
        after=client.get(f'/api/matches/{mid}').json()['players'][0]['x']
        assert after==before+1
        with client.websocket_connect(f'/ws/matches/{mid}') as ws:
            payload=ws.receive_json()
            assert set(payload['views'])=={'0'}
            assert 'visible' in payload['state']
        client.post(f'/api/matches/{mid}/control',json={'stop':True})
