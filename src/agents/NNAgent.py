import numpy as np
from torch import nn, tensor
from torch.distributions import Categorical

from src.agents.Agent import Agent


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    nn.init.orthogonal_(layer.weight, std)
    nn.init.constant_(layer.bias, bias_const)
    return layer


class NNAgent(nn.Module, Agent):
    def __init__(self, observation_shape, action_size, hidden_size=128):
        super().__init__()
        self.observation_shape = observation_shape
        self.action_size = action_size
        self.critic = nn.Sequential(
            layer_init(nn.Linear(np.array(observation_shape).prod(), hidden_size)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_size, hidden_size)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_size, 1), std=1.0),
        )
        self.actor = nn.Sequential(
            layer_init(nn.Linear(np.array(observation_shape).prod(), hidden_size)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_size, hidden_size)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_size, action_size), std=0.01),
        )

    def get_value(self, observations):
        return self.critic(observations)

    def get_probs(self, observations, action_masks):
        logits = self.actor(observations)
        if action_masks is not None:
            logits[~action_masks.bool()] = -1e8
        probs = Categorical(logits=logits)
        return probs

    def get_actions(self, observations: tensor, action_masks: tensor = None):
        probs = self.get_probs(observations, action_masks)
        return probs.sample()

    def get_action_and_value(self, observations: tensor, action_masks: tensor = None, action=None):
        probs = self.get_probs(observations, action_masks)
        if action is None:
            action = probs.sample()
        return action, probs.log_prob(action), probs.entropy(), self.critic(observations)

    def forward(self, inputs: tensor):
        observation, action_mask = inputs[:, :-self.action_size], inputs[:, -self.action_size:]
        print(observation.shape, action_mask.shape)
        print(observation, action_mask)
        return self.get_actions(observation, action_mask)
