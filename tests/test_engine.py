import copy
import pytest
from arena.engine import Game, line_visible
from arena.runner import Match
from arena.sdk import ACTIONS, RULES_VERSION
from arena.bots import BomberBot, danger_tiles, path_action


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


@pytest.mark.parametrize("shot,escape",[
    ((6,7,1,0),"move_n"),
    ((8,7,-1,0),"move_n"),
    ((7,6,0,1),"move_e"),
    ((7,8,0,-1),"move_e"),
])
def test_blaster_hits_target_that_vacates_its_next_tile(shot,escape):
    g=empty_game();owner,target=g.players
    owner.x,owner.y=3,3
    target.x,target.y=7,7
    x,y,dx,dy=shot
    g.projectiles=[{"x":x,"y":y,"dx":dx,"dy":dy,"owner":owner.id}]

    g.step({target.id:escape})

    assert (target.x,target.y)!=(7,7)
    assert target.hp==2 and target.damage_taken==1
    assert owner.damage_dealt==1
    assert not g.projectiles


def test_blaster_still_hits_stationary_target_and_is_absorbed():
    g=empty_game();owner,target=g.players
    owner.x,owner.y=3,5;target.x,target.y=5,5
    g.projectiles=[{"x":4,"y":5,"dx":1,"dy":0,"owner":owner.id}]

    g.step({})

    assert target.hp==2 and owner.damage_dealt==1
    assert not g.projectiles


def test_blaster_hits_player_moving_onto_its_vacated_tile():
    g=empty_game();owner,target=g.players
    owner.x,owner.y=1,5;target.x,target.y=4,5
    g.projectiles=[{"x":4,"y":5,"dx":1,"dy":0,"owner":owner.id}]

    g.step({target.id:"move_w"})

    assert (target.x,target.y)==(3,5)
    assert target.hp==2 and owner.damage_dealt==1
    assert not g.projectiles


def test_blaster_is_absorbed_by_first_player_in_its_step():
    g=empty_game(3);owner,first,second=g.players
    owner.x,owner.y=3,5;first.x,first.y=5,5;second.x,second.y=6,5
    g.projectiles=[{"x":5,"y":5,"dx":1,"dy":0,"owner":owner.id}]

    g.step({})

    assert first.hp==2 and second.hp==3
    assert owner.damage_dealt==1
    assert not g.projectiles


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


def test_full_axis_blast_reaches_all_four_corridor_ends():
    g=empty_game()
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({})
    cells={(f["x"],f["y"]) for f in g.flames}
    assert cells=={(x,7) for x in range(1,14)} | {(7,y) for y in range(1,14)}
    assert {f["expires_at"] for f in g.flames}=={4}
    assert len({f["explosion_id"] for f in g.flames})==1


def test_full_axis_blast_stops_at_wall_and_first_crate():
    g=empty_game();g.board[7][10]="#";g.board[7][3]="+";g.board[7][2]="+"
    cells=set(g.blast_tiles({"x":7,"y":7}))
    assert (9,7) in cells and (10,7) not in cells and (11,7) not in cells
    assert (3,7) in cells and (2,7) not in cells


def test_long_distance_chain_reaction():
    g=empty_game()
    g.bombs=[{"x":3,"y":7,"owner":0,"explode_at":1},
             {"x":11,"y":7,"owner":1,"explode_at":50}]
    g.step({})
    assert not g.bombs and len({f["explosion_id"] for f in g.flames})==2
    assert (11,1) in {(f["x"],f["y"]) for f in g.flames}


def test_flames_last_three_ticks_without_repeated_damage():
    g=empty_game();p=g.players[1];p.x,p.y=5,7
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    first=g.step({})
    assert p.hp==1 and p.damage_taken==2 and g.players[0].damage_dealt==2
    g.step({1:"move_e"})
    g.step({})
    assert g.flames and p.hp==1 and p.damage_taken==2
    g.step({})
    assert not g.flames and not g._explosion_hits and p.hp==1
    # Recorded frames must not change as active flames age out.
    assert first["flames"] and first["flames"][0]["expires_at"]==4


def test_late_flame_entry_takes_damage_once():
    g=empty_game();p=g.players[1];p.x,p.y=5,6
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({})
    assert p.hp==3
    g.step({1:"move_s"})
    assert p.hp==1 and g.players[0].damage_dealt==2
    g.step({})
    assert p.hp==1 and p.damage_taken==2


def test_leaving_and_reentering_same_explosion_does_not_hit_again():
    g=empty_game();p=g.players[1];p.x,p.y=5,7
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({});g.step({1:"move_n"});g.step({1:"move_s"})
    assert g.flames and p.hp==1 and p.damage_taken==2


def test_entry_on_last_active_tick_and_expiry_boundary():
    g=empty_game(3)
    a,b=g.players[1:];a.x,a.y=5,6;b.x,b.y=9,6
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({});g.step({});g.step({1:"move_s"})
    assert a.hp==1 and b.hp==3 and g.flames
    g.step({2:"move_s"})
    assert b.hp==3 and not g.flames


def test_lingering_flame_kill_retains_owner_credit():
    g=empty_game();p=g.players[1];p.x,p.y,p.hp=5,6,2
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({});g.step({1:"move_s"})
    assert not p.alive and g.players[0].kills==1 and g.winner==0


def test_shield_absorbs_explosion_only_once():
    g=empty_game();p=g.players[1];p.x,p.y,p.shield=5,7,True
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({})
    assert p.hp==3 and not p.shield
    g.step({});g.step({})
    assert p.hp==3 and p.damage_taken==0 and g.players[0].damage_dealt==0


def test_distinct_overlapping_explosions_each_hit():
    g=empty_game(3);p=g.players[2];p.x,p.y=5,7
    g.bombs=[{"x":3,"y":7,"owner":0,"explode_at":1},
             {"x":11,"y":7,"owner":1,"explode_at":1}]
    g.step({})
    assert not p.alive and p.damage_taken==3
    assert g.players[0].damage_dealt==g.players[1].damage_dealt==2
    assert g.players[0].kills==1


def test_bomb_planted_on_lingering_flames_chains_immediately():
    g=empty_game();p=g.players[0];p.x,p.y,p.weapon,p.shield=5,7,"bomb",True
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({})
    assert p.hp==3
    g.step({0:"fire_n"})
    assert not g.bombs and p.hp==1
    assert {f["expires_at"] for f in g.flames}=={4,5}
    assert len({f["explosion_id"] for f in g.flames})==2


def test_respawn_protection_blocks_flames_until_it_expires():
    g=empty_game(mode="deathmatch");p=g.players[1];p.x,p.y,p.protection=5,7,3
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({});g.step({})
    assert p.hp==3
    g.step({})
    assert p.protection==0 and p.hp==1


def test_respawn_waits_for_flames_if_no_safe_floor_exists():
    g=empty_game(mode="deathmatch")
    g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    g.step({})
    p=g.players[1];p.alive,p.hp,p.respawn_at=False,0,2
    g.board=[["#"]*15 for _ in range(15)]
    g.board[1][1]=g.board[7][7]="."
    g.step({});g.step({})
    assert not p.alive
    g.step({})
    assert p.alive and (p.x,p.y)==(7,7)


def test_bot_danger_matches_full_axis_and_flame_expiry():
    g=empty_game();g.bombs=[{"x":7,"y":7,"owner":0,"explode_at":1}]
    obs=g.observe(0,full=True)
    assert danger_tiles(obs)==set(g.blast_tiles(g.bombs[0]))
    g.step({})
    obs=g.observe(0,full=True)
    assert (13,7) in danger_tiles(obs)
    assert all(set(f)=={"x","y","owner","explosion_id","expires_at"} for f in obs["flames"])
    g.step({});g.step({})
    assert not danger_tiles(g.observe(0,full=True))


def test_escape_path_avoids_active_flames_even_from_danger():
    g=empty_game();p=g.players[0];p.x,p.y=5,5
    obs=g.observe(0,full=True)
    obs["bombs"]=[{"x":5,"y":5,"owner":0,"explode_at":10}]
    obs["flames"]=[{"x":5,"y":4,"owner":1,"explosion_id":1,"expires_at":3}]
    assert path_action(obs,{(5,3)},avoid=False)!="move_n"
    obs["flames"][0]["expires_at"]=1
    assert path_action(obs,{(5,3)},avoid=False)=="move_n"


def test_bomber_targets_opponent_beyond_old_radius():
    g=empty_game();a,b=g.players;a.x,a.y,a.weapon=5,7,"bomb";b.x,b.y=12,7
    assert BomberBot().choose_action(g.observe(0,full=True))=="fire_n"


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


def test_elimination_timeout_tiebreaks_by_health_then_damage():
    g=empty_game(max_ticks=1);g.players[0].damage_dealt=99;g.players[1].hp=2
    g.step({})
    assert g.done and g.result=="win" and g.winner==0

    g=empty_game(max_ticks=1);g.players[1].damage_dealt=1
    g.step({})
    assert g.winner==1

    g=empty_game(max_ticks=1)
    g.step({})
    assert g.result=="draw" and g.winner is None


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
    assert m.replay()["rules_version"]==RULES_VERSION=="0.4"
    clone=Game([p.name for p in m.game.players],71,max_ticks=60)
    for actions in m.action_log: clone.step(actions)
    assert clone.snapshot()==result


def test_invalid_actions_recorded_as_wait():
    g=empty_game();p=g.players[0]
    g.step({0:"teleport"})
    assert p.invalid_actions==1 and (p.x,p.y)==(1,1)
