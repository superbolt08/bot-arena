import copy
import pytest
from arena.engine import Game, line_visible
from arena.runner import Match
from arena.sdk import ACTIONS


def empty_game(n=2,mode="elimination",max_ticks=450):
    g=Game([f"Bot {i}" for i in range(n)],mode=mode,max_ticks=max_ticks)
    g.board=[["#" if x in (0,14) or y in (0,14) else "." for x in range(15)] for y in range(15)]
    g.initial_board=copy.deepcopy(g.board)
    g.memories=[copy.deepcopy(g.board) for _ in range(n)]
    g.pickups={}
    return g


def test_seed_and_action_replay_are_deterministic():
    a,b=Game(["a","b","c"],812),Game(["a","b","c"],812)
    for tick in range(80):
        actions={i:ACTIONS[(tick+i*3)%len(ACTIONS)] for i in range(3)}
        assert a.step(actions)==b.step(actions)


def test_simultaneous_contested_destination_and_swap():
    g=empty_game();a,b=g.players;a.x,a.y=4,5;b.x,b.y=6,5
    g.step({0:"move_e",1:"move_w"})
    assert (a.x,b.x)==(4,6)
    b.x=5
    g.step({0:"move_e",1:"move_w"})
    assert (a.x,b.x)==(4,5)


def test_failed_move_propagates_to_following_player():
    g=empty_game(3);a,b,c=g.players
    a.x,a.y=3,5;b.x,b.y=4,5;c.x,c.y=6,5
    g.step({0:"move_e",1:"move_e",2:"move_w"})
    assert [p.x for p in g.players]==[3,4,6]


def test_simultaneous_lethal_shots_produce_draw():
    g=empty_game();a,b=g.players
    a.x,a.y,a.hp=4,5,1;b.x,b.y,b.hp=5,5,1
    g.step({0:"fire_e",1:"fire_w"})
    assert g.done and g.result=="draw"
    assert a.kills==b.kills==1


def test_blast_chain_and_crate_stops_propagation():
    g=empty_game();g.board[5][8]="+"
    g.bombs=[{"x":3,"y":5,"owner":0,"explode_at":1},{"x":6,"y":5,"owner":1,"explode_at":50}]
    g.step({})
    assert not g.bombs
    cells={(f["x"],f["y"]) for f in g.flames}
    assert (8,5) in cells and (9,5) not in cells
    assert g.board[5][8]=="."


def test_bomb_fuse_and_owner_damage():
    g=empty_game();p=g.players[0];p.x,p.y,p.weapon=5,5,"bomb"
    g.step({0:"fire_n"})
    for _ in range(9): g.step({})
    assert p.hp==3
    g.step({})
    assert p.hp==1 and not g.bombs


def test_bomb_owner_can_leave_but_not_reenter():
    g=empty_game();p=g.players[0];p.x,p.y,p.weapon=5,5,"bomb"
    g.step({0:"fire_n"});g.step({0:"move_e"});g.step({0:"move_w"})
    assert (p.x,p.y)==(6,5)


def test_visibility_blocks_opponents_and_stale_terrain():
    g=empty_game();a,b=g.players;a.x,a.y=3,3;b.x,b.y=7,3
    g.board[3][5]="+"
    obs=g.observe(0)
    assert not obs["opponents"]
    assert obs["board"][3][5]=="+"
    g.board[3][8]="+" # Unseen change must not be leaked.
    assert g.observe(0)["board"][3][8]=="."
    g.board[3][5]="."
    assert g.observe(0)["opponents"][0]["id"]==1
    assert g.observe(0)["board"][3][8]=="+"


def test_no_diagonal_corner_peeking():
    g=empty_game();g.board[3][4]="#"
    assert not line_visible(g.board,(3,3),(4,4))
    g.board[3][4]="."
    assert line_visible(g.board,(3,3),(4,4))


def test_timeout_is_draw_even_with_health_lead():
    g=empty_game(max_ticks=1);g.players[1].hp=1
    g.step({})
    assert g.done and g.result=="draw" and g.winner is None


def test_deathmatch_respawn_and_score():
    g=empty_game(mode="deathmatch",max_ticks=20)
    a,b=g.players;a.x,a.y=4,5;b.x,b.y,b.hp=5,5,1
    g.step({0:"fire_e"})
    assert not b.alive and not g.done and a.kills==1
    for _ in range(15):g.step({})
    assert b.alive and b.hp==3 and b.protection>0
    for _ in range(4):g.step({})
    assert g.done and g.winner==0


def test_health_and_shield():
    g=empty_game();a,b=g.players;a.x,a.y,a.hp=4,5,1;b.x,b.y=6,5
    g.pickups[(4,5)]="health";g.step({});assert a.hp==2
    a.shield=True;g.step({1:"fire_w"});g.step({})
    assert a.hp==2 and not a.shield


def test_switch_does_not_reset_cooldown():
    g=empty_game();p=g.players[0];g.step({0:"fire_e"})
    assert p.cooldown==5
    g.step({0:"switch"});g.step({0:"switch"})
    assert p.cooldown==3


@pytest.mark.parametrize("count",[2,3,4])
def test_reference_matches_finish_and_replay(count):
    ids=["survivor","hunter","bomber","random"][:count]
    m=Match(ids,seed=71,max_ticks=60)
    result=m.run()
    assert result["done"] and len(result["players"])==count
    clone=Game([p.name for p in m.game.players],71,max_ticks=60)
    for actions in m.action_log: clone.step(actions)
    assert clone.snapshot()==result


def test_invalid_actions_recorded_as_wait():
    g=empty_game();p=g.players[0]
    g.step({0:"teleport"})
    assert p.invalid_actions==1 and (p.x,p.y)==(1,1)
