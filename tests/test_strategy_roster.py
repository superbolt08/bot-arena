import copy
import importlib.util
from pathlib import Path

import pytest

from arena.engine import Game
from arena.runner import Match
from arena.sdk import DIRECTIONS
from examples.strategy_roster import ROSTER, StrategyBot, export_roster


def bot(strategy):
    return type("TestStrategy", (StrategyBot,), {"strategy": strategy})()


def duel():
    game = Game(["Strategy", "Opponent"], seed=100)
    game.board = [["#" if x in (0, 14) or y in (0, 14) else "." for x in range(15)] for y in range(15)]
    game.initial_board = copy.deepcopy(game.board)
    game.memories = [copy.deepcopy(game.board) for _ in game.players]
    game.pickups = {}
    game.players[0].x, game.players[0].y = 5, 5
    game.players[1].x, game.players[1].y = 8, 5
    return game


def test_crossfire_plants_escapes_and_fires_blaster_before_bomb_explodes():
    game, candidate = duel(), bot("combo")
    game.players[0].weapon = "bomb"
    assert candidate.choose_action(game.observe(0)) == "fire_n"
    game.step({0: "fire_n"})
    for _ in range(2):
        action = candidate.choose_action(game.observe(0))
        assert action.startswith("move_")
        game.step({0: action})
    game.step({1: "move_n"})  # Opponent also leaves the bomb's row.
    assert candidate.choose_action(game.observe(0)) == "switch"
    game.step({0: "switch"})
    assert candidate.choose_action(game.observe(0)) == "fire_e"
    game.step({0: "fire_e"})
    assert any(b["owner"] == 0 for b in game.bombs)
    assert any(p["owner"] == 0 for p in game.projectiles)
    assert game.players[0].damage_taken == 0


def test_crossfire_takes_a_finishing_blaster_shot_before_arming_bomb():
    game = duel()
    game.players[1].hp = 1
    assert bot("combo").choose_action(game.observe(0)) == "fire_e"


def test_breach_bombs_crates_only_while_no_enemy_is_visible():
    game, candidate = duel(), bot("breach")
    game.board[5][7] = "#"  # Opponent is screened by terrain.
    game.board[3][5] = "+"
    observation = game.observe(0)
    assert not observation["opponents"]
    assert candidate.choose_action(observation) == "switch"
    game.step({0: "switch"})
    assert candidate.choose_action(game.observe(0)) == "fire_n"


def test_breach_switches_on_enemy_contact_instead_of_planting():
    game, candidate = duel(), bot("breach")
    game.board[3][5] = "+"
    game.players[0].weapon = "bomb"
    assert candidate.choose_action(game.observe(0)) == "switch"
    game.step({0: "switch"})
    assert candidate.choose_action(game.observe(0)) == "fire_e"
    assert not game.bombs


def test_breach_escapes_imminent_blast_before_switching_on_contact():
    game = duel()
    game.players[0].weapon = "bomb"
    game.bombs = [{"x": 5, "y": 5, "owner": 0, "explode_at": 2}]
    assert bot("breach").choose_action(game.observe(0)).startswith("move_")


def test_range_keeper_backs_off_during_reload_while_combo_holds_close_lane():
    game = duel()
    game.players[1].x = 7
    game.players[0].cooldown = 3
    action = bot("ranged").choose_action(game.observe(0))
    assert action.startswith("move_")
    dx, dy = DIRECTIONS[action[-1]]
    assert abs(5 + dx - 7) + abs(5 + dy - 5) > 2
    assert bot("combo").choose_action(game.observe(0)) == "wait"


@pytest.mark.parametrize("strategy", ROSTER)
def test_all_strategies_remember_hidden_bombs_and_leave_observations_unchanged(strategy):
    game, candidate = duel(), bot(strategy)
    game.bombs = [{"x": 5, "y": 5, "owner": 1, "explode_at": 10}]
    observation = game.observe(0)
    original = copy.deepcopy(observation)
    candidate.choose_action(observation)
    assert observation == original
    observation["tick"] = 1
    observation["bombs"] = []
    observation["entity_visible"][5][5] = False
    candidate.choose_action(observation)
    assert candidate.known_bombs[(5, 5, 1)]["explode_at"] == 10


def test_exports_include_frozen_helpers_and_preserve_edited_bundles(tmp_path):
    manifest = export_roster(tmp_path)
    assert len(manifest["bots"]) == 4
    for entry in manifest["bots"]:
        path = tmp_path / entry["file"]
        source = path.read_text()
        assert "from examples" not in source
        assert "class ThreatMap:" in source
        spec = importlib.util.spec_from_file_location("exported_strategy", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.Bot().strategy == entry["strategy"]
    edited = tmp_path / manifest["bots"][0]["file"]
    edited.write_text("# participant edits\n")
    with pytest.raises(FileExistsError):
        export_roster(tmp_path)
    assert edited.read_text() == "# participant edits\n"


@pytest.mark.parametrize("strategy", ("ranged", "siege"))
def test_specialists_never_fire_the_other_weapon(strategy):
    game, candidate = duel(), bot(strategy)
    fired = []
    for _ in range(50):
        action = candidate.choose_action(game.observe(0))
        if action.startswith("fire_"):
            fired.append(game.players[0].weapon)
        game.step({0: action})
        if game.done:
            break
    assert fired
    assert set(fired) == ({"blaster"} if strategy == "ranged" else {"bomb"})


@pytest.mark.parametrize("strategy", ROSTER)
def test_exported_bot_works_through_actual_upload_worker(tmp_path, strategy):
    manifest = export_roster(tmp_path)
    entry = next(e for e in manifest["bots"] if e["strategy"] == strategy)
    match = Match(["strategy", "hunter"], {"strategy": {"name": entry["name"], "path": str(tmp_path / entry["file"])}},
                  seed=61000, max_ticks=40, record=False)
    try:
        match.run()
        assert not match.errors
        assert match.game.players[0].invalid_actions == 0
    finally:
        match.close()
