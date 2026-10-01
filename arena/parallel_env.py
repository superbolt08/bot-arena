"""Optional PettingZoo ParallelEnv adapter. Install pettingzoo to use it."""
import numpy as np
from pettingzoo import ParallelEnv
from gymnasium.spaces import Box, Discrete
from .engine import Game
from .bots import features
from .sdk import ACTIONS


class ArenaEnv(ParallelEnv):
    metadata={"name":"bot_arena_v0","render_modes":[]}
    def __init__(self,players=2,max_ticks=450):
        self.possible_agents=[f"bot_{i}" for i in range(players)]
        self.max_ticks=max_ticks
        self.render_mode=None
        self.observation_spaces={a:Box(low=0,high=900,shape=(8,),dtype=np.float32) for a in self.possible_agents}
        self.action_spaces={a:Discrete(len(ACTIONS)) for a in self.possible_agents}
        self.agents=[]

    def observation_space(self,agent): return self.observation_spaces[agent]
    def action_space(self,agent): return self.action_spaces[agent]
    def _obs(self,a): return np.asarray(features(self.game.observe(self.possible_agents.index(a))),dtype=np.float32)

    def reset(self,seed=None,options=None):
        self.game=Game(self.possible_agents,42 if seed is None else seed,max_ticks=self.max_ticks)
        self.agents=self.possible_agents[:]
        return {a:self._obs(a) for a in self.agents},{a:{} for a in self.agents}

    def step(self,actions):
        active=self.agents[:]
        self.game.step({self.possible_agents.index(a):ACTIONS[int(actions[a])] for a in active})
        observations={a:self._obs(a) for a in active}
        rewards={a:0.0 for a in active}
        terminations={a:False for a in active}
        truncations={a:False for a in active}
        infos={a:{} for a in active}
        for a in active:
            pid=self.possible_agents.index(a)
            dead=not self.game.players[pid].alive
            if dead: rewards[a]=-1.0
            if self.game.winner==pid: rewards[a]=1.0
            # The configured match clock is a game-rule terminal draw, not a training cutoff.
            terminations[a]=dead or self.game.done
        self.agents=[a for a in active if not terminations[a] and not truncations[a]]
        return observations,rewards,terminations,truncations,infos
