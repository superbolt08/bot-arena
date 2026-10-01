import pytest

pytest.importorskip("pettingzoo")
from pettingzoo.test import parallel_api_test
from arena.parallel_env import ArenaEnv


def test_parallel_contract_and_terminal_draw():
    parallel_api_test(ArenaEnv(players=4,max_ticks=25),num_cycles=50)
    env=ArenaEnv(max_ticks=1)
    obs,info=env.reset(seed=4)
    obs,rewards,terminated,truncated,info=env.step({a:0 for a in env.agents})
    assert all(terminated.values()) and not any(truncated.values())
    assert all(v==0 for v in rewards.values()) and not env.agents
