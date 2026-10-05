import os
import shutil
import requests
from pathlib import Path
from datasets import load_dataset
from PIL import Image
from io import BytesIO
import sys
from tqdm import tqdm
import random

DATASET_DIR = Path("ml/dataset")
TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "validation"
TEST_DIR = DATASET_DIR / "test"

BASE_URL = "https://github.com/spMohanty/PlantVillage-Dataset/raw/master/"

VAL_SPLIT = 0.15
SEED = 42

def clear_directory(dir_path):
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)

def download_image(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            img.verify()
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
    return None

def main():
    print("Loading PlantVillage dataset from Hugging Face...")
    print("Using default configuration")
    
    try:
        dataset = load_dataset("mohanty/PlantVillage", "default")
        print("Dataset loaded successfully!")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)
    
    print(f"Dataset splits: {list(dataset.keys())}")
    
    train_paths = dataset['train']['text']
    test_paths = dataset['test']['text']
    
    print(f"Train samples: {len(train_paths)}")
    print(f"Test samples: {len(test_paths)}")
    
    def parse_class(path):
        parts = path.split('/')
        if len(parts) >= 3:
            return parts[2]
        return None
    
    train_classes = [parse_class(p) for p in train_paths]
    test_classes = [parse_class(p) for p in test_paths]
    
    all_classes = sorted(set(train_classes + test_classes))
    all_classes = [c for c in all_classes if c is not None]
    
    print(f"Total classes: {len(all_classes)}")
    print(f"First 10 classes: {all_classes[:10]}")
    
    class_to_idx = {cls: idx for idx, cls in enumerate(all_classes)}
    
    for dir_path in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        clear_directory(dir_path)
    
    for class_name in all_classes:
        (TRAIN_DIR / class_name).mkdir(parents=True, exist_ok=True)
        (VAL_DIR / class_name).mkdir(parents=True, exist_ok=True)
        (TEST_DIR / class_name).mkdir(parents=True, exist_ok=True)
    
    random.seed(SEED)
    train_val_data = list(zip(train_paths, train_classes))
    random.shuffle(train_val_data)
    
    val_size = int(len(train_val_data) * VAL_SPLIT)
    val_data = train_val_data[:val_size]
    train_data = train_val_data[val_size:]
    
    print(f"\nSplit sizes:")
    print(f"  Train: {len(train_data)}")
    print(f"  Validation: {len(val_data)}")
    print(f"  Test: {len(test_paths)}")
    
    def process_split(data, split_dir, split_name):
        count = 0
        failed = 0
        for i, (path, class_name) in enumerate(tqdm(data, desc=f"Downloading {split_name}")):
            if class_name is None:
                failed += 1
                continue
            
            url = BASE_URL + path.replace(' ', '%20')
            class_dir = split_dir / class_name
            image_path = class_dir / f"{split_name}_{i:06d}.jpg"
            
            try:
                img = download_image(url)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(image_path, "JPEG", quality=95)
                count += 1
            except Exception as e:
                print(f"  Failed to download {path}: {e}")
                failed += 1
        
        print(f"  {split_name}: {count} images downloaded, {failed} failed")
        return count, failed
    
    train_count, train_failed = process_split(train_data, TRAIN_DIR, "train")
    val_count, val_failed = process_split(val_data, VAL_DIR, "validation")
    test_count, test_failed = process_split(list(zip(test_paths, test_classes)), TEST_DIR, "test")
    
    total = train_count + val_count + test_count
    total_failed = train_failed + val_failed + test_failed
    
    print("\n" + "="*50)
    print("Dataset preparation complete")
    print("="*50)
    print(f"Train images: {train_count}")
    print(f"Validation images: {val_count}")
    print(f"Test images: {test_count}")
    print(f"Total images: {total}")
    print(f"Failed downloads: {total_failed}")
    print(f"Number of classes: {len(all_classes)}")
    print(f"First 10 class names: {all_classes[:10]}")
    
    print("\nVerifying directory structure...")
    for split_name, split_dir in [("train", TRAIN_DIR), ("validation", VAL_DIR), ("test", TEST_DIR)]:
        class_dirs = [d for d in split_dir.iterdir() if d.is_dir()]
        total_images = sum(len(list(d.glob("*.jpg"))) for d in class_dirs)
        print(f"{split_name}: {len(class_dirs)} class directories, {total_images} images")
        
        if total_images == 0:
            print(f"  WARNING: {split_name} has no images!")
    
    if train_count == 0 or val_count == 0 or test_count == 0:
        print("\nERROR: One or more splits have no images!")
        sys.exit(1)

if __name__ == "__main__":
    main()