import os
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import numpy as np


class CropDiseaseDataset(Dataset):
    def __init__(
        self,
        root_dir: str,
        transform: Optional[transforms.Compose] = None,
        class_to_idx: Optional[Dict[str, int]] = None,
    ):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples: List[Tuple[str, int]] = []
        self.classes: List[str] = []
        self.class_to_idx: Dict[str, int] = {}
        self.idx_to_class: Dict[int, str] = {}

        if not self.root_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {root_dir}")

        class_dirs = sorted([d for d in self.root_dir.iterdir() if d.is_dir()])
        if not class_dirs:
            raise ValueError(f"No class directories found in {root_dir}")

        if class_to_idx is None:
            self.classes = [d.name for d in class_dirs]
            self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        else:
            self.class_to_idx = class_to_idx
            self.classes = [None] * len(class_to_idx)
            for cls, idx in class_to_idx.items():
                self.classes[idx] = cls

        self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}

        for class_dir in class_dirs:
            class_name = class_dir.name
            if class_name not in self.class_to_idx:
                continue
            class_idx = self.class_to_idx[class_name]
            for img_path in class_dir.glob("*"):
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                    self.samples.append((str(img_path), class_idx))

        if not self.samples:
            raise ValueError(f"No valid images found in {root_dir}")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to load image {img_path}: {e}")

        if self.transform:
            image = self.transform(image)

        return image, label


def get_train_transforms(image_size: int = 224) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize((image_size + 32, image_size + 32)),
        transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def get_val_transforms(image_size: int = 224) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def get_test_transforms(image_size: int = 224) -> transforms.Compose:
    return get_val_transforms(image_size)


def create_dataloaders(
    dataset_root: str,
    batch_size: int = 32,
    num_workers: int = 4,
    image_size: int = 224,
) -> Tuple[DataLoader, DataLoader, DataLoader, List[str], Dict[str, int]]:
    train_dir = Path(dataset_root) / "train"
    val_dir = Path(dataset_root) / "validation"
    test_dir = Path(dataset_root) / "test"

    if not train_dir.exists():
        raise FileNotFoundError(f"Training directory not found: {train_dir}")

    train_dataset = CropDiseaseDataset(
        str(train_dir),
        transform=get_train_transforms(image_size),
    )

    class_to_idx = train_dataset.class_to_idx
    classes = train_dataset.classes

    val_dataset = None
    val_loader = None
    if val_dir.exists():
        try:
            val_dataset = CropDiseaseDataset(
                str(val_dir),
                transform=get_val_transforms(image_size),
                class_to_idx=class_to_idx,
            )
            val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=True,
            )
        except ValueError:
            pass

    test_dataset = None
    test_loader = None
    if test_dir.exists():
        try:
            test_dataset = CropDiseaseDataset(
                str(test_dir),
                transform=get_test_transforms(image_size),
                class_to_idx=class_to_idx,
            )
            test_loader = DataLoader(
                test_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=True,
            )
        except ValueError:
            pass

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )

    return train_loader, val_loader, test_loader, classes, class_to_idx


def save_class_names(class_names: List[str], output_path: str) -> None:
    with open(output_path, "w") as f:
        json.dump(class_names, f, indent=2)


def load_class_names(input_path: str) -> List[str]:
    with open(input_path, "r") as f:
        return json.load(f)


def preprocess_single_image(
    image_path: str,
    image_size: int = 224,
) -> torch.Tensor:
    transform = get_test_transforms(image_size)
    image = Image.open(image_path).convert("RGB")
    return transform(image).unsqueeze(0)