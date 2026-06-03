"""Small training script for local CPU/GPU test.

Usage:
    python train.py

The script loads up to 100 breath segments using `NafasDataset` and trains
the `nafas_model` for a few epochs. `device` is imported from the model so
the same code will automatically run on GPU if available.
"""

import argparse

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from app.model import nafas_model, device
from app.dataset import NafasDiseaseDataset
from app.clinical_model import train_and_save_rf
from app.nlp_model import train_nlp


def train_local_model(max_samples=250, epochs=5):
    # Print which device will be used (CPU or CUDA GPU)
    print(f"--- Starting Training on: {device} ---")

    # 1. Load Data. `max_samples <= 0` (or None) loads every breath segment
    # found under data/ — used for a full-dataset train.
    # We use batch_size=1 because breath segments vary in time length.
    # The model uses AdaptiveAvgPool2d to handle different spatial sizes.
    scope = "FULL dataset" if (max_samples is None or max_samples <= 0) else f"{max_samples} samples"
    print(f"--- Loading {scope} (this can take a few minutes for the full set) ---")
    dataset = NafasDiseaseDataset(data_dir="data", max_samples=max_samples)
    print(f"--- Loaded {len(dataset)} breath segments ---")
    dataloader = DataLoader(dataset, batch_size=1, shuffle=True)

    # 2. Setup Loss and Optimizer
    criterion = nn.CrossEntropyLoss()  # suitable for multi-class classification
    optimizer = optim.Adam(nafas_model.parameters(), lr=0.001)

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
    parser = argparse.ArgumentParser(description="Train the Nafas base models.")
    parser.add_argument("--full", action="store_true",
                        help="Train the audio CNN on the FULL dataset (every breath segment).")
    parser.add_argument("--max-samples", type=int, default=250,
                        help="Cap on audio segments when not using --full (default 250).")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Number of training epochs for the audio CNN (default 5).")
    args = parser.parse_args()

    max_samples = 0 if args.full else args.max_samples

    # Train the clinical Random Forest first (fast). If data is missing,
    # print a helpful message and continue to train the audio CNN.
    try:
        train_and_save_rf()
    except Exception as e:
        print(f"Clinical model training skipped: {e}")

    # Train the lightweight NLP model (creates nlp_weights.pkl)
    try:
        train_nlp()
    except Exception as e:
        print(f"NLP training skipped: {e}")

    train_local_model(max_samples=max_samples, epochs=args.epochs)
