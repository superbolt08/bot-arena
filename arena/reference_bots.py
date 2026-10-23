"""Built-in app roster, including the standard and extended reference bots."""
from .bots import BOT_INFO as BASE_BOT_INFO, BUILTINS as BASE_BUILTINS
from examples.hit_and_run_bot import Bot as HitAndRunBot
from examples.strategy_roster import StrategyBot


class CrossfireBot(StrategyBot):
    strategy = "combo"


class BreachAndShootBot(StrategyBot):
    strategy = "breach"


class RangeKeeperBot(StrategyBot):
    strategy = "ranged"


BUILTINS = {
    **BASE_BUILTINS,
    "hit_and_run": HitAndRunBot,
    "crossfire": CrossfireBot,
    "breach_shoot": BreachAndShootBot,
    "range_keeper": RangeKeeperBot,
}

BOT_INFO = [
    *BASE_BOT_INFO,
    {"id": "hit_and_run", "name": "Hit and Run", "style": "Scout, shoot, retreat · bomb memory", "color": "#75c4e8"},
    {"id": "crossfire", "name": "Crossfire", "style": "Bomb pressure · blaster follow-up", "color": "#f4d779"},
    {"id": "breach_shoot", "name": "Breach & Shoot", "style": "Bomb crates · blaster on contact", "color": "#f3a66f"},
    {"id": "range_keeper", "name": "Range Keeper", "style": "Blaster only · keep opponents at range", "color": "#d796df"},
]
