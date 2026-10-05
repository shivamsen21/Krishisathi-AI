import os
import json
import argparse
import shutil
from pathlib import Path
from datasets import load_dataset
from PIL import Image
from tqdm import tqdm
import sys

def verify_image(image_path: Path) -> bool:
    try:
        with Image.open(image_path) as img:
            img.verify()
        with Image.open(image_path) as img:
            img.load()
        return True
    except Exception:
        return False

def save_class_names(class_names, output_path: str):
    with open(output_path, "w") as f:
        json.dump(class_names, f, indent=2)

def prepare_dataset(
    dataset_root: str = "ml/dataset",
    max_images_per_class: int = None,
    val_split: float = 0.15,
    seed: int = 42,
):
    import random
    random.seed(seed)

    print("Loading PlantVillage dataset from Hugging Face...")
    dataset = load_dataset("mohanty/PlantVillage", "default")
    
    class_names = sorted(dataset["train"].features["label"].names)
    num_classes = len(class_names)
    print(f"Detected {num_classes} classes: {class_names}")

    dataset_root = Path(dataset_root)
    train_dir = dataset_root / "train"
    val_dir = dataset_root / "validation"
    test_dir = dataset_root / "test"

    if train_dir.exists():
        shutil.rmtree(train_dir)
    if val_dir.exists():
        shutil.rmtree(val_dir)
    if test_dir.exists():
        shutil.rmtree(test_dir)

    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    for class_name in class_names:
        (train_dir / class_name).mkdir(parents=True, exist_ok=True)
        (val_dir / class_name).mkdir(parents=True, exist_ok=True)
        (test_dir / class_name).mkdir(parents=True, exist_ok=True)

    print("\nProcessing training data...")
    train_data = dataset["train"]
    class_to_indices = {i: [] for i in range(num_classes)}
    
    for idx, example in enumerate(train_data):
        label = example["label"]
        class_to_indices[label].append(idx)

    train_counts = {class_name: 0 for class_name in class_names}
    val_counts = {class_name: 0 for class_name in class_names}
    corrupted_train = 0
    corrupted_val = 0

    for class_idx, indices in class_to_indices.items():
        class_name = class_names[class_idx]
        random.shuffle(indices)
        
        num_val = max(1, int(len(indices) * val_split))
        val_indices = set(indices[:num_val])
        train_indices = indices[num_val:]

        if max_images_per_class:
            train_indices = train_indices[:max_images_per_class]
            val_indices = list(val_indices)[:max_images_per_class]

        for idx in tqdm(train_indices, desc=f"Train: {class_name}", leave=False):
            example = train_data[int(idx)]
            image = example["image"]
            save_path = train_dir / class_name / f"train_{idx}.jpg"
            try:
                image.save(save_path, "JPEG", quality=95)
                if verify_image(save_path):
                    train_counts[class_name] += 1
                else:
                    save_path.unlink(missing_ok=True)
                    corrupted_train += 1
            except Exception:
                corrupted_train += 1

        for idx in tqdm(val_indices, desc=f"Val: {class_name}", leave=False):
            example = train_data[int(idx)]
            image = example["image"]
            save_path = val_dir / class_name / f"val_{idx}.jpg"
            try:
                image.save(save_path, "JPEG", quality=95)
                if verify_image(save_path):
                    val_counts[class_name] += 1
                else:
                    save_path.unlink(missing_ok=True)
                    corrupted_val += 1
            except Exception:
                corrupted_val += 1

    print("\nProcessing test data...")
    test_data = dataset["test"]
    test_counts = {class_name: 0 for class_name in class_names}
    corrupted_test = 0

    test_class_to_indices = {i: [] for i in range(num_classes)}
    for idx, example in enumerate(test_data):
        label = example["label"]
        test_class_to_indices[label].append(idx)

    for class_idx, indices in test_class_to_indices.items():
        class_name = class_names[class_idx]
        
        if max_images_per_class:
            indices = indices[:max_images_per_class]

        for idx in tqdm(indices, desc=f"Test: {class_name}", leave=False):
            example = test_data[int(idx)]
            image = example["image"]
            save_path = test_dir / class_name / f"test_{idx}.jpg"
            try:
                image.save(save_path, "JPEG", quality=95)
                if verify_image(save_path):
                    test_counts[class_name] += 1
                else:
                    save_path.unlink(missing_ok=True)
                    corrupted_test += 1
            except Exception:
                corrupted_test += 1

    save_class_names(class_names, "ml/class_names.json")
    print(f"\nClass names saved to: ml/class_names.json")

    total_train = sum(train_counts.values())
    total_val = sum(val_counts.values())
    total_test = sum(test_counts.values())

    print("\n" + "="*60)
    print("Dataset preparation complete")
    print("="*60)
    print(f"Training images:   {total_train}")
    print(f"Validation images: {total_val}")
    print(f"Test images:       {total_test}")
    print(f"Number of classes: {num_classes}")
    print()
    print("Classes:")
    for class_name in class_names:
        print(f"  {class_name}: train={train_counts[class_name]}, val={val_counts[class_name]}, test={test_counts[class_name]}")
    
    if corrupted_train > 0 or corrupted_val > 0 or corrupted_test > 0:
        print(f"\nCorrupted images removed:")
        print(f"  Train: {corrupted_train}")
        print(f"  Validation: {corrupted_val}")
        print(f"  Test: {corrupted_test}")

    empty_classes = []
    for class_name in class_names:
        if train_counts[class_name] == 0 and val_counts[class_name] == 0 and test_counts[class_name] == 0:
            empty_classes.append(class_name)
    
    if empty_classes:
        print(f"\nWARNING: Empty classes detected: {empty_classes}")

    print("\nVerifying dataset structure...")
    verify_dataset(dataset_root, class_names)

def verify_dataset(dataset_root: Path, class_names: list):
    train_dir = dataset_root / "train"
    val_dir = dataset_root / "validation"
    test_dir = dataset_root / "test"

    all_good = True
    
    for split_name, split_dir in [("train", train_dir), ("validation", val_dir), ("test", test_dir)]:
        if not split_dir.exists():
            print(f"  {split_name}: Directory missing!")
            all_good = False
            continue
            
        for class_name in class_names:
            class_dir = split_dir / class_name
            if not class_dir.exists():
                print(f"  {split_name}/{class_name}: Directory missing!")
                all_good = False
                continue
                
            images = list(class_dir.glob("*"))
            if not images:
                print(f"  {split_name}/{class_name}: Empty!")
                all_good = False
                continue
                
            for img_path in images:
                if not verify_image(img_path):
                    print(f"  {split_name}/{class_name}/{img_path.name}: Corrupted!")
                    all_good = False
    
    if all_good:
        print("  All checks passed!")
    else:
        print("  Some issues found (see above)")

def main():
    parser = argparse.ArgumentParser(description="Prepare PlantVillage dataset for AgroVision AI")
    parser.add_argument("--data", type=str, default="ml/dataset", help="Dataset root directory")
    parser.add_argument("--max-images-per-class", type=int, default=None, help="Limit images per class (for testing)")
    parser.add_argument("--val-split", type=float, default=0.15, help="Validation split ratio from training data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    prepare_dataset(
        dataset_root=args.data,
        max_images_per_class=args.max_images_per_class,
        val_split=args.val_split,
        seed=args.seed,
    )

if __name__ == "__main__":
    main()