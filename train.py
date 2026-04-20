"""Small training script for local CPU/GPU test.

Usage:
    python train.py

The script loads up to 100 breath segments using `NafasDataset` and trains
the `nafas_model` for a few epochs. `device` is imported from the model so
the same code will automatically run on GPU if available.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from app.model import nafas_model, device
from app.dataset import NafasDataset


def train_local_model():
    # Print which device will be used (CPU or CUDA GPU)
    print(f"--- Starting Training on: {device} ---")

    # 1. Load Data (Limit to 100 samples)
    # We use batch_size=1 because breath segments vary in time length.
    # The model uses AdaptiveAvgPool2d to handle different spatial sizes.
    dataset = NafasDataset(data_dir="data", max_samples=250)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=True)

    # 2. Setup Loss and Optimizer
    criterion = nn.CrossEntropyLoss()  # suitable for multi-class classification
    optimizer = optim.Adam(nafas_model.parameters(), lr=0.001)

    epochs = 5  # small number for a quick CPU smoke test

    # 3. Training loop
    nafas_model.train()

    for epoch in range(epochs):
        running_loss = 0.0
        correct_predictions = 0

        for inputs, labels in dataloader:
            # inputs shape: [batch, channels, height, width]
            # Move tensors to the selected device (CPU/GPU)
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            # Forward pass
            outputs = nafas_model(inputs)

            # Compute loss and backpropagate
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # Accumulate metrics
            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            # For batch_size=1 this adds either 0 or 1 per sample; using .sum() keeps it robust.
            correct_predictions += (predicted == labels).sum().item()

        # Compute epoch statistics (guard against empty dataloader)
        if len(dataloader) > 0:
            epoch_loss = running_loss / len(dataloader)
            epoch_acc = (correct_predictions / len(dataloader)) * 100
        else:
            epoch_loss = 0.0
            epoch_acc = 0.0

        print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.2f}%")

    # 4. Persist model weights
    torch.save(nafas_model.state_dict(), "nafas_weights.pth")
    print("\nTraining complete! Model saved as 'nafas_weights.pth'")


if __name__ == "__main__":
    train_local_model()
