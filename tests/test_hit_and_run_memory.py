import copy
from pathlib import Path

from arena.engine import Game
from arena.runner import Match
from examples.hit_and_run_bot import Bot


def corner_game():
    game = Game(["hitnrun3 Memory Fix", "Opponent"], seed=101)
    game.board = [["#" if x in (0, 14) or y in (0, 14) or (x % 2 == 0 and y % 2 == 0)
                   else "." for x in range(15)] for y in range(15)]
    game.initial_board = copy.deepcopy(game.board)
    game.memories = [copy.deepcopy(game.board) for _ in game.players]
    game.pickups = {}
    game.players[0].x, game.players[0].y = 7, 7
    game.players[1].x, game.players[1].y = 1, 1
    game.bombs = [{"x": 5, "y": 7, "owner": 1, "explode_at": 10}]
    return game


def test_seen_enemy_bomb_is_not_forgotten_after_rounding_a_corner():
    game, bot = corner_game(), Bot()
    assert game.observe(0)["bombs"]
    action = bot.choose_action(game.observe(0))
    assert action == "move_n"
    game.step({0: action})
    assert not game.observe(0)["bombs"]
    while game.tick < 13:
        action = bot.choose_action(game.observe(0))
        if game.tick < 12:
            assert action != "move_s"  # Returning to row 7 is still unsafe.
        game.step({0: action})
    assert game.players[0].damage_taken == 0
    bot.choose_action(game.observe(0))
    assert not bot.enemy_bombs and not bot.enemy_flames


def test_player_screen_does_not_turn_a_hidden_bomb_into_an_explosion():
    game, bot = corner_game(), Bot()
    observation = game.observe(0)
    bot._observation_with_enemy_bomb_memory(observation)
    observation["tick"] = 2
    observation["bombs"] = []
    observation["visible"][7][5] = True
    observation["entity_visible"][7][5] = False
    result = bot._observation_with_enemy_bomb_memory(observation)
    assert result["bombs"] == [{"x": 5, "y": 7, "owner": 1, "explode_at": 10}]
    assert not result["flames"]


def test_confirmed_early_disappearance_keeps_flames_for_their_remaining_lifetime():
    game, bot = corner_game(), Bot()
    observation = game.observe(0)
    bot._observation_with_enemy_bomb_memory(observation)
    observation["tick"] = 4
    observation["bombs"] = []
    observation["entity_visible"][7][5] = True
    result = bot._observation_with_enemy_bomb_memory(observation)
    assert not result["bombs"]
    assert any((f["x"], f["y"], f["expires_at"]) == (7, 7, 7) for f in result["flames"])
    observation["tick"] = 6
    result = bot._observation_with_enemy_bomb_memory(observation)
    assert not result["flames"]  # They expire before the next action at tick 7.


def test_enemy_chain_timing_survives_loss_of_sight():
    game, bot = corner_game(), Bot()
    observation = game.observe(0)
    observation["bombs"].append({"x": 9, "y": 7, "owner": 2, "explode_at": 30})
    result = bot._observation_with_enemy_bomb_memory(observation)
    assert {b["explode_at"] for b in result["bombs"]} == {10}
    observation["tick"] = 10
    observation["bombs"] = []
    observation["entity_visible"][7][5] = False
    observation["entity_visible"][7][9] = False
    result = bot._observation_with_enemy_bomb_memory(observation)
    assert not result["bombs"]
    assert {f["expires_at"] for f in result["flames"]} == {13}


def test_memory_does_not_mutate_observations_or_leak_between_bot_instances():
    observation = corner_game().observe(0)
    original = copy.deepcopy(observation)
    bot = Bot()
    bot._observation_with_enemy_bomb_memory(observation)
    assert observation == original
    assert Bot().enemy_bombs == {}


def test_updated_file_runs_in_the_upload_worker():
    source = Path(__file__).resolve().parents[1] / "examples" / "hit_and_run_bot.py"
    match = Match(["fixed", "hunter"], {"fixed": {"name": "Memory Fix", "path": str(source)}},
                  seed=10000, max_ticks=80, record=False)
    try:
        match.run()
        assert not match.errors
        assert match.game.players[0].invalid_actions == 0
    finally:
        match.close()
