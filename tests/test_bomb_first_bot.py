import copy
from pathlib import Path

from arena.engine import Game
from arena.runner import ExternalBot
from arena.sdk import ACTIONS
from examples.bomb_first_bot import Bot, ThreatMap


def duel(corridor=False):
    game = Game(["Bomb First", "Opponent"], seed=100)
    game.board = [["#" if x in (0, 14) or y in (0, 14) or (corridor and y != 5) else "."
                   for x in range(15)] for y in range(15)]
    game.initial_board = copy.deepcopy(game.board)
    game.memories = [copy.deepcopy(game.board) for _ in game.players]
    game.pickups = {}
    game.players[0].x, game.players[0].y = 5, 5
    game.players[1].x, game.players[1].y = 8, 5
    return game


def test_bomb_opportunity_takes_priority_over_an_available_blaster_shot():
    game, bot = duel(), Bot()
    assert bot.choose_action(game.observe(0)) == "switch"
    game.step({0: "switch"})
    assert bot.choose_action(game.observe(0)) == "fire_n"


def test_plant_escape_and_switch_to_blaster_without_self_damage():
    game, bot = duel(), Bot()
    game.players[0].weapon = "bomb"
    assert bot.choose_action(game.observe(0)) == "fire_n"
    game.step({0: "fire_n"})
    actions = []
    for _ in range(13):
        action = bot.choose_action(game.observe(0))
        actions.append(action)
        game.step({0: action})
        if game.done:
            break
    assert actions[0].startswith("move_")
    assert "switch" in actions
    assert game.players[0].damage_taken == 0
    assert game.players[0].self_bomb_deaths == 0


def test_no_escape_uses_blaster_instead_of_planting_in_a_dead_end():
    game, bot = duel(corridor=True), Bot()
    game.players[0].weapon = "bomb"
    assert bot.choose_action(game.observe(0)) == "switch"
    game.step({0: "switch"})
    assert bot.choose_action(game.observe(0)) == "fire_e"


def test_safe_refuge_uses_blaster_while_owned_bomb_is_active():
    game, bot = duel(), Bot()
    game.players[0].x, game.players[0].y, game.players[0].weapon = 4, 4, "bomb"
    game.players[1].x, game.players[1].y = 8, 4
    game.bombs = [{"x": 5, "y": 5, "owner": 0, "explode_at": 10}]
    assert bot.choose_action(game.observe(0)) == "switch"
    game.step({0: "switch"})
    assert bot.choose_action(game.observe(0)) == "fire_e"


def test_blast_reaches_beyond_three_tiles_and_includes_chain_timing():
    game = duel()
    observation = game.observe(0)
    bombs = [{"x": 2, "y": 5, "owner": 1, "explode_at": 2},
             {"x": 9, "y": 5, "owner": 0, "explode_at": 11}]
    threats = ThreatMap(observation, bombs)
    assert threats.due == [2, 2]
    assert not threats.safe((9, 2), 2)
    assert threats.safe((9, 2), 5)
    assert threats.escape(start_delay=1, max_moves=6, deadline=0) is None


def test_expiring_flames_do_not_retroactively_chain_a_new_bomb():
    game = duel()
    game.tick = 4
    observation = game.observe(0)
    threats = ThreatMap(observation, [
        {"x": 2, "y": 5, "owner": 1, "explode_at": 2},
        {"x": 5, "y": 5, "owner": 0, "explode_at": 15},
    ])
    assert threats.due == [2, 15]


def test_escape_does_not_route_through_lingering_flames():
    game = duel()
    observation = game.observe(0)
    observation["flames"] = [{"x": 5, "y": 4, "expires_at": 4}]
    threats = ThreatMap(observation, [{"x": 5, "y": 5, "owner": 0, "explode_at": 10}])
    assert threats.escape() != "move_n"
    assert not threats.can_move((5, 5), (5, 4), 1)
    assert threats.safe((5, 4), 4)


def test_hidden_bomb_is_remembered_until_its_flames_expire():
    game, bot = duel(), Bot()
    observation = game.observe(0)
    observation["bombs"] = [{"x": 6, "y": 5, "owner": 1, "explode_at": 10}]
    bot.remember_bombs(observation)
    observation["bombs"] = []
    observation["tick"] = 5
    observation["entity_visible"][5][6] = False
    bot.remember_bombs(observation)
    assert bot.known_bombs[(6, 5, 1)]["explode_at"] == 10
    observation["tick"] = 13
    bot.remember_bombs(observation)
    assert not bot.known_bombs


def test_blaster_control_keeps_movement_policy_but_never_selects_bombs():
    game, bot = duel(), Bot()
    bot.use_bombs = False
    assert bot.choose_action(game.observe(0)) == "fire_e"


def test_uploadable_bot_runs_through_the_worker_protocol():
    source = Path(__file__).resolve().parents[1] / "examples" / "bomb_first_bot.py"
    worker = ExternalBot(source)
    try:
        import time
        worker.send(duel().observe(0))
        response = worker.receive(time.monotonic() + .1)
        assert response["action"] in ACTIONS
        assert not worker.error
    finally:
        worker.close()
