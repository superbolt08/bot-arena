from unittest.mock import patch
from examples.parameter_bot import Bot, PARAMETERS
from arena.engine import Game
from arena.runner import Match, ROOT


def observation():
    obs=Game(['Student','Opponent']).observe(0,full=True)
    obs['self'].update(x=5,y=5,hp=2,cooldown=0)
    obs['opponents']=[dict(obs['opponents'][0],x=5,y=9)]
    obs['pickups']=[{'x':4,'y':5,'kind':'health'}]
    obs['bombs']=[]
    obs['projectiles']=[]
    obs['flames']=[]
    obs['board']=[['.']*15 for _ in range(15)]
    return obs


def test_parameter_changes_can_change_the_decision_without_rewriting_helpers():
    bot=Bot();obs=observation()
    with patch('examples.parameter_bot.act_for_mode',side_effect=lambda o,mode:mode):
        assert bot.choose_action(obs)=='attack'
        bot.parameters['retreat_health']=2
        assert bot.choose_action(obs)=='supply'
        bot.parameters['retreat_health']=1
        bot.parameters['pickup_priority']=0.9
        assert bot.choose_action(obs)=='supply'
    assert PARAMETERS['retreat_health']==1


def test_known_danger_takes_priority_over_preferences():
    obs=observation();obs['bombs']=[{'x':5,'y':5,'owner':0,'explode_at':10}]
    with patch('examples.parameter_bot.act_for_mode',side_effect=lambda o,mode:mode):
        assert Bot().choose_action(obs)=='escape'


def test_parameter_starter_runs_in_the_real_upload_worker():
    match=Match(['student','hunter'],{'student':{'path':str(ROOT/'examples/parameter_bot.py'),'name':'Student'}},max_ticks=25)
    try:
        match.run()
        assert not match.errors
        assert match.game.players[0].invalid_actions==0
    finally:
        match.close()
