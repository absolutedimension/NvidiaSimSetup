# Stage A vision-PPO networks for skrl.
#
# Observation layout (single flat tensor coming from the env):
#   state[12] = lin_vel(3) + ang_vel(3) + projected_gravity(3) + desired_pos_b(3)
#   depth[84*84] = forward depth camera, flattened row-major
#
# Both policy and value share the same trunk architecture but separate weights
# (skrl convention with `separate: True` semantics — we instantiate two Models).

from __future__ import annotations

import torch
import torch.nn as nn

from skrl.models.torch import DeterministicMixin, GaussianMixin, Model

from .quadcopter_corridor_v1_env_cfg import DEPTH_H, DEPTH_W, STATE_DIM


def _build_vision_cnn(out_dim: int) -> nn.Sequential:
    # Tiny CNN: 84x84x1 -> ~64-dim latent. Sized roughly like DeepMind drone work.
    return nn.Sequential(
        nn.Conv2d(1, 16, kernel_size=5, stride=2),   # 40x40
        nn.ReLU(inplace=True),
        nn.Conv2d(16, 32, kernel_size=5, stride=2),  # 18x18
        nn.ReLU(inplace=True),
        nn.Conv2d(32, 32, kernel_size=3, stride=2),  # 8x8
        nn.ReLU(inplace=True),
        nn.Flatten(),
        nn.Linear(32 * 8 * 8, out_dim),
        nn.ReLU(inplace=True),
    )


class _SharedTrunk(nn.Module):
    """State MLP + depth CNN -> concatenated 128-dim feature."""

    def __init__(self, state_dim: int = STATE_DIM, vision_dim: int = 64, mlp_dim: int = 64):
        super().__init__()
        self.state_dim = state_dim
        self.vision_dim = vision_dim
        self.state_mlp = nn.Sequential(
            nn.Linear(state_dim, mlp_dim),
            nn.ELU(inplace=True),
            nn.Linear(mlp_dim, mlp_dim),
            nn.ELU(inplace=True),
        )
        self.vision_cnn = _build_vision_cnn(vision_dim)
        self.out_dim = mlp_dim + vision_dim

    def forward(self, flat_obs: torch.Tensor) -> torch.Tensor:
        # flat_obs: (N, STATE_DIM + DEPTH_H*DEPTH_W)
        state = flat_obs[:, : self.state_dim]
        depth = flat_obs[:, self.state_dim :].reshape(-1, 1, DEPTH_H, DEPTH_W)
        s_feat = self.state_mlp(state)
        v_feat = self.vision_cnn(depth)
        return torch.cat([s_feat, v_feat], dim=-1)


class VisionPolicy(GaussianMixin, Model):
    def __init__(
        self,
        observation_space,
        action_space,
        device,
        clip_actions: bool = False,
        clip_log_std: bool = True,
        min_log_std: float = -20.0,
        max_log_std: float = 2.0,
        initial_log_std: float = 0.0,
    ):
        Model.__init__(self, observation_space, action_space, device)
        GaussianMixin.__init__(
            self,
            clip_actions=clip_actions,
            clip_log_std=clip_log_std,
            min_log_std=min_log_std,
            max_log_std=max_log_std,
        )
        self.trunk = _SharedTrunk()
        self.head = nn.Sequential(
            nn.Linear(self.trunk.out_dim, 128),
            nn.ELU(inplace=True),
            nn.Linear(128, self.num_actions),
        )
        self.log_std_parameter = nn.Parameter(initial_log_std * torch.ones(self.num_actions))

    def compute(self, inputs, role):
        feat = self.trunk(inputs["states"])
        return self.head(feat), self.log_std_parameter, {}


class VisionValue(DeterministicMixin, Model):
    def __init__(self, observation_space, action_space, device, clip_actions: bool = False):
        Model.__init__(self, observation_space, action_space, device)
        DeterministicMixin.__init__(self, clip_actions=clip_actions)
        self.trunk = _SharedTrunk()
        self.head = nn.Sequential(
            nn.Linear(self.trunk.out_dim, 128),
            nn.ELU(inplace=True),
            nn.Linear(128, 1),
        )

    def compute(self, inputs, role):
        feat = self.trunk(inputs["states"])
        return self.head(feat), {}
