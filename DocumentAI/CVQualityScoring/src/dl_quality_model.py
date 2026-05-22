"""PyTorch MLP model for CV quality scoring."""

from __future__ import annotations

import torch
from torch import nn


class CvQualityMlp(nn.Module):
    """Predicts a 0-100 CV quality score from text and structural features."""

    def __init__(self, input_size: int, dropout: float = 0.25) -> None:
        """Create the feed-forward layers for text+numeric quality features."""
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """Return one continuous 0-100 quality score prediction per CV."""
        return self.network(inputs).squeeze(1)
