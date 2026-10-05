import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

from preprocessing import create_dataloaders, load_class_names
from model import create_model, MobileNetV2CropDisease


def load_model(
    model_path: str,
    class_names_path: str,
    device: torch.device,
) -> Tuple[MobileNetV2CropDisease, List[str], Dict[str, int]]:
    checkpoint = torch.load(model_path, map_location=device)
    class_names = load_class_names(class_names_path)
    num_classes = len(class_names)
    class_to_idx = {cls: idx for idx, cls in enumerate(class_names)}

    model = create_model(
        num_classes=num_classes,
        pretrained=False,
        freeze_backbone=False,
        device=device,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, class_names, class_to_idx


def evaluate(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
    class_names: List[str],
) -> Dict:
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(outputs, 1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)

    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average="macro", zero_division=0)
    recall = recall_score(all_labels, all_preds, average="macro", zero_division=0)
    f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)

    cm = confusion_matrix(all_labels, all_preds)
    report = classification_report(all_labels, all_preds, target_names=class_names, zero_division=0, output_dict=True)

    per_class_metrics = {}
    for i, cls in enumerate(class_names):
        if str(i) in report:
            per_class_metrics[cls] = {
                "precision": report[str(i)]["precision"],
                "recall": report[str(i)]["recall"],
                "f1": report[str(i)]["f1-score"],
                "support": int(report[str(i)]["support"]),
            }

    return {
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "confusion_matrix": cm.tolist(),
        "per_class_metrics": per_class_metrics,
        "predictions": all_preds.tolist(),
        "labels": all_labels.tolist(),
        "probabilities": all_probs.tolist(),
    }


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    output_path: str,
    normalize: bool = True,
) -> None:
    if normalize:
        cm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm)
        fmt = ".2f"
        vmax = 1.0
    else:
        fmt = "d"
        vmax = None

    plt.figure(figsize=(max(10, len(class_names) * 0.5), max(8, len(class_names) * 0.4)))
    sns.heatmap(
        cm,
        annot=True,
        fmt=fmt,
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        vmin=0,
        vmax=vmax,
        cbar_kws={"label": "Normalized Frequency" if normalize else "Count"},
    )
    plt.title("Confusion Matrix" + (" (Normalized)" if normalize else ""))
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Confusion matrix saved to: {output_path}")


def save_results(results: Dict, output_path: str) -> None:
    serializable_results = {
        "accuracy": results["accuracy"],
        "precision_macro": results["precision_macro"],
        "recall_macro": results["recall_macro"],
        "f1_macro": results["f1_macro"],
        "confusion_matrix": results["confusion_matrix"],
        "per_class_metrics": results["per_class_metrics"],
    }
    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2)
    print(f"Evaluation results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate MobileNetV2 Crop Disease Model")
    parser.add_argument("--model", type=str, default="ml/models/crop_disease_mobilenetv2.pth", help="Model checkpoint path")
    parser.add_argument("--class-names", type=str, default="ml/class_names.json", help="Class names JSON path")
    parser.add_argument("--data", type=str, default="ml/dataset", help="Dataset root directory")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--workers", type=int, default=4, help="Data loader workers")
    parser.add_argument("--image-size", type=int, default=224, help="Input image size")
    parser.add_argument("--device", type=str, default="auto", help="Device (auto, cpu, cuda)")
    parser.add_argument("--output-dir", type=str, default="ml/results", help="Output directory for results")

    args = parser.parse_args()

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    print(f"Using device: {device}")

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    try:
        model, class_names, class_to_idx = load_model(args.model, args.class_names, device)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error loading model: {e}")
        return 1

    try:
        _, _, test_loader, _, _ = create_dataloaders(
            dataset_root=args.data,
            batch_size=args.batch_size,
            num_workers=args.workers,
            image_size=args.image_size,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    if test_loader is None:
        print("Error: No test set found. Cannot evaluate.")
        return 1

    print(f"\nEvaluating on {len(test_loader.dataset)} test samples...")
    print(f"Classes: {class_names}")

    results = evaluate(model, test_loader, device, class_names)

    print(f"\n=== Evaluation Results ===")
    print(f"Accuracy:  {results['accuracy']:.4f}")
    print(f"Precision: {results['precision_macro']:.4f}")
    print(f"Recall:    {results['recall_macro']:.4f}")
    print(f"F1-Score:  {results['f1_macro']:.4f}")

    print("\nPer-class metrics:")
    for cls, metrics in results["per_class_metrics"].items():
        print(f"  {cls}: P={metrics['precision']:.4f} R={metrics['recall']:.4f} F1={metrics['f1']:.4f} (n={metrics['support']})")

    cm = np.array(results["confusion_matrix"])
    plot_confusion_matrix(cm, class_names, os.path.join(args.output_dir, "confusion_matrix.png"), normalize=True)
    plot_confusion_matrix(cm, class_names, os.path.join(args.output_dir, "confusion_matrix_raw.png"), normalize=False)

    save_results(results, os.path.join(args.output_dir, "evaluation_results.json"))

    print("\nEvaluation completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())