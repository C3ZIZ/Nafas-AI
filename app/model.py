import os
from pathlib import Path

import torch
import torch.nn as nn


class NafasCNN(nn.Module):
    def __init__(self):
        super(NafasCNN, self).__init__()

        # Extract local time-frequency patterns from spectrograms.
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )

        self.pool = nn.AdaptiveAvgPool2d((4, 4))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 8),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = self.classifier(x)
        return x


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
nafas_model = NafasCNN().to(device)

# Load pretrained weights if they exist; ignore otherwise so the API can boot
# and the auto-trainer can populate them at startup.
_WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "nafas_weights.pth"
if _WEIGHTS_PATH.exists():
    try:
        nafas_model.load_state_dict(torch.load(str(_WEIGHTS_PATH), map_location=device))
        nafas_model.eval()
    except Exception as _e:  # corrupt or shape-mismatched weights — keep random init
        print(f"[model] Could not load nafas_weights.pth: {_e}")


def reload_weights() -> bool:
    """Reload `nafas_weights.pth` from disk. Used by the auto-trainer after training."""
    if not _WEIGHTS_PATH.exists():
        return False
    try:
        nafas_model.load_state_dict(torch.load(str(_WEIGHTS_PATH), map_location=device))
        nafas_model.eval()
        return True
    except Exception as e:
        print(f"[model] reload_weights failed: {e}")
        return False

