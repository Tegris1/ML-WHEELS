"""Different Reward Systems for ML Models."""
import numpy as np
from abc import ABC, abstractmethod

class RewardSystem(ABC):
    @abstractmethod
    def compute_reward(self, state, action, next_state, done, info=None): pass

class SparseReward(RewardSystem):
    def __init__(self, success_reward=1.0, failure_penalty=-0.1):
        self.success_reward = success_reward
        self.failure_penalty = failure_penalty
    def compute_reward(self, state, action, next_state, done, info=None):
        if not done: return 0.0
        return self.success_reward if (info and info.get("success")) else self.failure_penalty

class DenseReward(RewardSystem):
    def __init__(self, goal_state=None, step_penalty=-0.01):
        self.goal_state = goal_state
        self.step_penalty = step_penalty
    def compute_reward(self, state, action, next_state, done, info=None):
        if self.goal_state is not None:
            return float(np.linalg.norm(state - self.goal_state) - np.linalg.norm(next_state - self.goal_state)) + self.step_penalty
        return self.step_penalty

class CuriosityReward(RewardSystem):
    def __init__(self, scale=1.0):
        self.scale = scale
        self.predicted = {}
    def compute_reward(self, state, action, next_state, done, info=None):
        key = (state.tobytes(), action)
        if key in self.predicted:
            error = np.linalg.norm(next_state - self.predicted[key])
            reward = self.scale * error
        else:
            reward = self.scale
        self.predicted[key] = next_state
        return float(reward)
