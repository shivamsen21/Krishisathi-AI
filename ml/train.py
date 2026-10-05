import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingLR
import numpy as np

from preprocessing import create_dataloaders, save_class_names
from model import create_model, MobileNetV2CropDisease


class EarlyStopping:
    def __init__(self, patience: int = 10, min_delta: float = 1e-4, mode: str = "min"):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False

    def __call__(self, score: float) -> bool:
        if self.mode == "min":
            score = -score
        if self.best_score is None:
            self.best_score = score
            return False
        if score < self.best_score + self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.counter = 0
        return self.early_stop


def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = 100.0 * correct / total
    return epoch_loss, epoch_acc


def validate(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = 100.0 * correct / total
    return epoch_loss, epoch_acc


def train(
    dataset_root: str,
    model_save_path: str,
    class_names_path: str,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    fine_tune_lr: float = 1e-4,
    freeze_epochs: int = 5,
    fine_tune_epochs: int = 15,
    patience: int = 10,
    num_workers: int = 4,
    image_size: int = 224,
    device: str = "auto",
) -> Dict:
    if device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device)

    print(f"Using device: {device}")

    train_loader, val_loader, _, classes, class_to_idx = create_dataloaders(
        dataset_root=dataset_root,
        batch_size=batch_size,
        num_workers=num_workers,
        image_size=image_size,
    )

    if val_loader is None:
        print("Warning: No validation set found. Using training set for validation (not recommended).")
        val_loader = train_loader

    num_classes = len(classes)
    print(f"Detected {num_classes} classes: {classes}")

    save_class_names(classes, class_names_path)
    print(f"Class names saved to: {class_names_path}")

    model = create_model(
        num_classes=num_classes,
        pretrained=True,
        freeze_backbone=True,
        device=device,
    )

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.AdamW(
        model.get_classifier_params(),
        lr=lr,
        weight_decay=1e-4,
    )

    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3, verbose=True)
    early_stopping = EarlyStopping(patience=patience, mode="min")

    best_val_loss = float("inf")
    best_model_state = None
    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
    }

    print(f"\n=== Phase 1: Training Classifier (Backbone Frozen) ===")
    print(f"Epochs: {freeze_epochs}, Learning Rate: {lr}")

    for epoch in range(freeze_epochs):
        start_time = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step(val_loss)

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        elapsed = time.time() - start_time
        print(
            f"Epoch {epoch+1}/{freeze_epochs} | "
            f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
            f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
            f"Time: {elapsed:.1f}s"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()

        if early_stopping(val_loss):
            print(f"Early stopping triggered at epoch {epoch+1}")
            break

    print(f"\n=== Phase 2: Fine-tuning (Backbone Unfrozen) ===")
    print(f"Epochs: {fine_tune_epochs}, Learning Rate: {fine_tune_lr}")

    model.unfreeze_backbone(num_layers=7)

    optimizer = optim.AdamW([
        {"params": model.get_backbone_params(), "lr": fine_tune_lr},
        {"params": model.get_classifier_params(), "lr": lr},
    ], weight_decay=1e-4)

    scheduler = CosineAnnealingLR(optimizer, T_max=fine_tune_epochs)
    early_stopping = EarlyStopping(patience=patience, mode="min")

    for epoch in range(fine_tune_epochs):
        start_time = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        elapsed = time.time() - start_time
        print(
            f"Epoch {epoch+1}/{fine_tune_epochs} | "
            f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
            f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
            f"Time: {elapsed:.1f}s"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()

        if early_stopping(val_loss):
            print(f"Early stopping triggered at epoch {epoch+1}")
            break

    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    torch.save({
        "model_state_dict": model.state_dict(),
        "num_classes": num_classes,
        "class_names": classes,
        "class_to_idx": class_to_idx,
        "history": history,
        "best_val_loss": best_val_loss,
    }, model_save_path)

    print(f"\nBest model saved to: {model_save_path}")
    print(f"Best validation loss: {best_val_loss:.4f}")

    return {
        "model_path": model_save_path,
        "class_names_path": class_names_path,
        "history": history,
        "best_val_loss": best_val_loss,
        "num_classes": num_classes,
        "classes": classes,
    }


def main():
    parser = argparse.ArgumentParser(description="Train MobileNetV2 for Crop Disease Detection")
    parser.add_argument("--data", type=str, default="ml/dataset", help="Dataset root directory")
    parser.add_argument("--model-out", type=str, default="ml/models/crop_disease_mobilenetv2.pth", help="Output model path")
    parser.add_argument("--class-names", type=str, default="ml/class_names.json", help="Output class names path")
    parser.add_argument("--epochs", type=int, default=50, help="Total epochs (freeze + fine-tune)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--fine-tune-lr", type=float, default=1e-4, help="Fine-tuning learning rate")
    parser.add_argument("--freeze-epochs", type=int, default=5, help="Epochs with frozen backbone")
    parser.add_argument("--fine-tune-epochs", type=int, default=15, help="Fine-tuning epochs")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--workers", type=int, default=4, help="Data loader workers")
    parser.add_argument("--image-size", type=int, default=224, help="Input image size")
    parser.add_argument("--device", type=str, default="auto", help="Device (auto, cpu, cuda)")

    args = parser.parse_args()

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.class_names).parent.mkdir(parents=True, exist_ok=True)

    try:
        result = train(
            dataset_root=args.data,
            model_save_path=args.model_out,
            class_names_path=args.class_names,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            fine_tune_lr=args.fine_tune_lr,
            freeze_epochs=args.freeze_epochs,
            fine_tune_epochs=args.fine_tune_epochs,
            patience=args.patience,
            num_workers=args.workers,
            image_size=args.image_size,
            device=args.device,
        )
        print("\nTraining completed successfully!")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please ensure the dataset exists with the following structure:")
        print("  ml/dataset/train/<class_name>/images...")
        print("  ml/dataset/validation/<class_name>/images...")
        print("  ml/dataset/test/<class_name>/images...")
        return 1
    except ValueError as e:
        print(f"\nError: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())