import os
import json
import random
import shutil
from pathlib import Path
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

def count_existing_images(dataset_root: Path, class_names: list) -> dict:
    counts = {
        "train": {c: 0 for c in class_names},
        "validation": {c: 0 for c in class_names},
        "test": {c: 0 for c in class_names}
    }
    
    for split_name in ["train", "validation", "test"]:
        split_dir = dataset_root / split_name
        if not split_dir.exists():
            continue
        for class_name in class_names:
            class_dir = split_dir / class_name
            if not class_dir.exists():
                continue
            for img_path in class_dir.glob("*"):
                if verify_image(img_path):
                    counts[split_name][class_name] += 1
    return counts

def get_existing_files(dataset_root: Path, class_name: str, split: str) -> set:
    existing = set()
    class_dir = dataset_root / split / class_name
    if not class_dir.exists():
        return existing
    for img_path in class_dir.glob("*"):
        existing.add(img_path.name)
    return existing

def prepare_dataset_resume(
    dataset_root: str = "ml/dataset",
    max_images_per_class: int = None,
    val_split: float = 0.15,
    seed: int = 42,
):
    random.seed(seed)
    
    data_dir = Path("data_extracted")
    train_split_file = Path("splits/color_train.txt")
    test_split_file = Path("splits/color_test.txt")
    
    if not data_dir.exists():
        print("ERROR: Extracted data not found. Please run data extraction first.")
        return
    if not train_split_file.exists() or not test_split_file.exists():
        print("ERROR: Split files not found.")
        return
    
    print("Reading split files...")
    with open(train_split_file) as f:
        train_paths = [line.strip() for line in f if line.strip()]
    with open(test_split_file) as f:
        test_paths = [line.strip() for line in f if line.strip()]
    
    print(f"Train images in split: {len(train_paths)}")
    print(f"Test images in split: {len(test_paths)}")
    
    class_names = sorted(set(p.split('/')[2] for p in train_paths + test_paths))
    num_classes = len(class_names)
    print(f"Detected {num_classes} classes")
    
    dataset_root = Path(dataset_root)
    train_dir = dataset_root / "train"
    val_dir = dataset_root / "validation"
    test_dir = dataset_root / "test"
    
    for class_name in class_names:
        (train_dir / class_name).mkdir(parents=True, exist_ok=True)
        (val_dir / class_name).mkdir(parents=True, exist_ok=True)
        (test_dir / class_name).mkdir(parents=True, exist_ok=True)
    
    print("\nChecking existing images...")
    existing_counts = count_existing_images(dataset_root, class_names)
    
    total_existing_train = sum(existing_counts["train"].values())
    total_existing_val = sum(existing_counts["validation"].values())
    total_existing_test = sum(existing_counts["test"].values())
    print(f"Existing - Train: {total_existing_train}, Val: {total_existing_val}, Test: {total_existing_test}")
    
    class_to_train_paths = {c: [] for c in class_names}
    for p in train_paths:
        class_name = p.split('/')[2]
        class_to_train_paths[class_name].append(p)
    
    class_to_test_paths = {c: [] for c in class_names}
    for p in test_paths:
        class_name = p.split('/')[2]
        class_to_test_paths[class_name].append(p)
    
    train_counts = {class_name: existing_counts["train"][class_name] for class_name in class_names}
    val_counts = {class_name: existing_counts["validation"][class_name] for class_name in class_names}
    test_counts = {class_name: existing_counts["test"][class_name] for class_name in class_names}
    corrupted_train = 0
    corrupted_val = 0
    corrupted_test = 0
    
    print("\nProcessing training data (creating validation split)...")
    total_train_to_process = 0
    total_val_to_process = 0
    
    for class_name in class_names:
        paths = class_to_train_paths[class_name]
        random.shuffle(paths)
        
        num_val = max(1, int(len(paths) * val_split))
        val_paths = paths[:num_val]
        train_paths_cls = paths[num_val:]
        
        if max_images_per_class:
            train_paths_cls = train_paths_cls[:max_images_per_class]
            val_paths = val_paths[:max_images_per_class]
        
        existing_train = get_existing_files(dataset_root, class_name, "train")
        existing_val = get_existing_files(dataset_root, class_name, "validation")
        
        train_remaining = [p for p in train_paths_cls if Path(p).name not in existing_train]
        val_remaining = [p for p in val_paths if Path(p).name not in existing_val]
        
        total_train_to_process += len(train_remaining)
        total_val_to_process += len(val_remaining)
    
    print(f"Total train images to process: {total_train_to_process}")
    print(f"Total val images to process: {total_val_to_process}")
    
    processed_train = 0
    processed_val = 0
    
    for class_name in class_names:
        paths = class_to_train_paths[class_name]
        random.shuffle(paths)
        
        num_val = max(1, int(len(paths) * val_split))
        val_paths = paths[:num_val]
        train_paths_cls = paths[num_val:]
        
        if max_images_per_class:
            train_paths_cls = train_paths_cls[:max_images_per_class]
            val_paths = val_paths[:max_images_per_class]
        
        existing_train = get_existing_files(dataset_root, class_name, "train")
        existing_val = get_existing_files(dataset_root, class_name, "validation")
        
        train_remaining = [p for p in train_paths_cls if Path(p).name not in existing_train]
        val_remaining = [p for p in val_paths if Path(p).name not in existing_val]
        
        print(f"\nClass: {class_name}")
        print(f"  Existing train: {len(existing_train)}, remaining: {len(train_remaining)}")
        print(f"  Existing val: {len(existing_val)}, remaining: {len(val_remaining)}")
        
        for rel_path in tqdm(train_remaining, desc=f"Train: {class_name}", leave=False):
            src = data_dir / rel_path
            dst = train_dir / class_name / Path(rel_path).name
            try:
                shutil.copy2(src, dst)
                if verify_image(dst):
                    train_counts[class_name] += 1
                    processed_train += 1
                else:
                    dst.unlink(missing_ok=True)
                    corrupted_train += 1
            except Exception as e:
                corrupted_train += 1
            
            if processed_train % 100 == 0 and processed_train > 0:
                pct = 100 * processed_train / total_train_to_process if total_train_to_process > 0 else 0
                print(f"  Overall train progress: {processed_train}/{total_train_to_process} ({pct:.1f}%)")
        
        for rel_path in tqdm(val_remaining, desc=f"Val: {class_name}", leave=False):
            src = data_dir / rel_path
            dst = val_dir / class_name / Path(rel_path).name
            try:
                shutil.copy2(src, dst)
                if verify_image(dst):
                    val_counts[class_name] += 1
                    processed_val += 1
                else:
                    dst.unlink(missing_ok=True)
                    corrupted_val += 1
            except Exception as e:
                corrupted_val += 1
            
            if processed_val % 100 == 0 and processed_val > 0:
                pct = 100 * processed_val / total_val_to_process if total_val_to_process > 0 else 0
                print(f"  Overall val progress: {processed_val}/{total_val_to_process} ({pct:.1f}%)")
    
    print("\nProcessing test data...")
    total_test_to_process = 0
    
    for class_name in class_names:
        paths = class_to_test_paths[class_name]
        if max_images_per_class:
            paths = paths[:max_images_per_class]
        existing_test = get_existing_files(dataset_root, class_name, "test")
        test_remaining = [p for p in paths if Path(p).name not in existing_test]
        total_test_to_process += len(test_remaining)
    
    print(f"Total test images to process: {total_test_to_process}")
    
    processed_test = 0
    for class_name in class_names:
        paths = class_to_test_paths[class_name]
        if max_images_per_class:
            paths = paths[:max_images_per_class]
        existing_test = get_existing_files(dataset_root, class_name, "test")
        test_remaining = [p for p in paths if Path(p).name not in existing_test]
        
        print(f"\nClass: {class_name}")
        print(f"  Existing test: {len(existing_test)}, remaining: {len(test_remaining)}")
        
        for rel_path in tqdm(test_remaining, desc=f"Test: {class_name}", leave=False):
            src = data_dir / rel_path
            dst = test_dir / class_name / Path(rel_path).name
            try:
                shutil.copy2(src, dst)
                if verify_image(dst):
                    test_counts[class_name] += 1
                    processed_test += 1
                else:
                    dst.unlink(missing_ok=True)
                    corrupted_test += 1
            except Exception as e:
                corrupted_test += 1
            
            if processed_test % 100 == 0 and processed_test > 0:
                pct = 100 * processed_test / total_test_to_process if total_test_to_process > 0 else 0
                print(f"  Overall test progress: {processed_test}/{total_test_to_process} ({pct:.1f}%)")
    
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
    import argparse
    parser = argparse.ArgumentParser(description="Resume PlantVillage dataset preparation for AgroVision AI")
    parser.add_argument("--data", type=str, default="ml/dataset", help="Dataset root directory")
    parser.add_argument("--max-images-per-class", type=int, default=None, help="Limit images per class (for testing)")
    parser.add_argument("--val-split", type=float, default=0.15, help="Validation split ratio from training data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    prepare_dataset_resume(
        dataset_root=args.data,
        max_images_per_class=args.max_images_per_class,
        val_split=args.val_split,
        seed=args.seed,
    )

if __name__ == "__main__":
    main()