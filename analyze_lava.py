#!/usr/bin/env python

import numpy as np
import torch as pt
import sys
import torch.nn as nn

from policies import rollout
import scenarios
from networks import PiNetTV, QNetTV

import seaborn as sns
import matplotlib.pyplot as plt

#np.random.seed(0)
#pt.manual_seed(0)

from torch.distributions.multivariate_normal import MultivariateNormal
from torch.distributions.uniform import Uniform

np.random.seed(0)
pt.manual_seed(0)

def sample_initial_dist():
    return Uniform(0, 5).sample()#np.random.normal(2.5, 0.1)

def sample_sensor_noise(cov):
    return MultivariateNormal(pt.zeros(1), pt.eye(1) * cov).sample()

scenario = scenarios.LavaScenario(sample_initial_dist, lambda: sample_sensor_noise(1))
ntrvs = 5
horizon = 5
batch_size = 50

def make_pi_sequence(t: int):
    return nn.Sequential(
        nn.Linear(ntrvs, 64),
        nn.ELU(),
        nn.Linear(64, 64),
        nn.ELU(),
        nn.Linear(64, scenario.ninputs * 2)
    )

def make_q_sequence(t: int):
    return nn.Sequential(
        nn.Linear(scenario.noutputs + ntrvs, 64),
        nn.ELU(),
        nn.Linear(64, 64),
        nn.ELU(),
        nn.Linear(64, ntrvs * 2)
    )


pi_net = PiNetTV(make_pi_sequence, horizon)
q_net = QNetTV(make_q_sequence, horizon)

loaded_models = pt.load(sys.argv[1])

pi_net.load_state_dict(loaded_models['pi_net_state_dict'])
q_net.load_state_dict(loaded_models['q_net_state_dict'])

states, outputs, trvs, inputs, costs = rollout(pi_net, q_net, ntrvs, scenario, horizon, batch_size)

print(f'Mean: {costs.sum(axis=0).mean().item()},\t Std: {costs.sum(axis=0).std().item()}')

for t in range(horizon + 1):
   plot_data = pt.stack((states[0, t, :], t * pt.ones(batch_size))).t().numpy()
   plt.scatter(x=plot_data[:, 0], y=plot_data[:, 1])

plt.xlabel('Position [m]')
plt.ylabel('Time [s]')
plt.show()
