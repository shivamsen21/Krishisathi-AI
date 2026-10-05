import os
import json
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

import torch
import torch.nn as nn
from PIL import Image

from preprocessing import preprocess_single_image, load_class_names
from model import create_model, MobileNetV2CropDisease


CONFIDENCE_THRESHOLD = 0.60


def load_model(
    model_path: str,
    class_names_path: str,
    device: torch.device,
) -> Tuple[MobileNetV2CropDisease, List[str]]:
    checkpoint = torch.load(model_path, map_location=device)
    class_names = load_class_names(class_names_path)
    num_classes = len(class_names)

    model = create_model(
        num_classes=num_classes,
        pretrained=False,
        freeze_backbone=False,
        device=device,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, class_names


def predict_image(
    model: nn.Module,
    image_tensor: torch.Tensor,
    class_names: List[str],
    device: torch.device,
    top_k: int = 3,
    threshold: float = 0.60,
) -> Dict[str, Any]:
    model.eval()
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1)
        top_probs, top_indices = torch.topk(probs, k=min(top_k, len(class_names)), dim=1)

    top_probs = top_probs.cpu().numpy()[0]
    top_indices = top_indices.cpu().numpy()[0]

    predictions = []
    for prob, idx in zip(top_probs, top_indices):
        predictions.append({
            "class": class_names[idx],
            "confidence": float(prob),
        })

    return {
        "top_predictions": predictions,
        "predicted_class": predictions[0]["class"],
        "confidence": predictions[0]["confidence"],
        "is_low_confidence": predictions[0]["confidence"] < threshold,
    }


def parse_crop_from_class(class_name: str) -> str:
    parts = class_name.split("___")
    if len(parts) >= 2:
        return parts[0].replace("_", " ").title()
    return class_name.replace("_", " ").title()


def format_disease_name(class_name: str) -> str:
    parts = class_name.split("___")
    if len(parts) >= 2:
        crop = parts[0].replace("_", " ").title()
        disease = parts[1].replace("_", " ").title()
        if "healthy" in disease.lower():
            return f"{crop} Healthy"
        return f"{crop} {disease}"
    return class_name.replace("_", " ").title()


def main():
    parser = argparse.ArgumentParser(description="Predict crop disease from leaf image")
    parser.add_argument("image_path", type=str, help="Path to leaf image")
    parser.add_argument("--model", type=str, default="ml/models/crop_disease_mobilenetv2.pth", help="Model checkpoint path")
    parser.add_argument("--class-names", type=str, default="ml/class_names.json", help="Class names JSON path")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top predictions to show")
    parser.add_argument("--threshold", type=float, default=CONFIDENCE_THRESHOLD, help="Confidence threshold")
    parser.add_argument("--device", type=str, default="auto", help="Device (auto, cpu, cuda)")

    args = parser.parse_args()

    threshold = args.threshold

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    print(f"Using device: {device}")

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        return 1

    try:
        model, class_names = load_model(args.model, args.class_names, device)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please train the model first using: python ml/train.py")
        return 1
    except Exception as e:
        print(f"Error loading model: {e}")
        return 1

    try:
        image_tensor = preprocess_single_image(str(image_path))
    except Exception as e:
        print(f"Error processing image: {e}")
        return 1

    result = predict_image(model, image_tensor, class_names, device, top_k=args.top_k, threshold=threshold)

    predicted_class = result["predicted_class"]
    confidence = result["confidence"]
    is_low_confidence = result["is_low_confidence"]
    top_predictions = result["top_predictions"]

    crop = parse_crop_from_class(predicted_class)
    disease = format_disease_name(predicted_class)

    print("\n" + "=" * 50)
    print("PREDICTION RESULT")
    print("=" * 50)
    print(f"Crop:       {crop}")
    print(f"Disease:    {disease}")
    print(f"Confidence: {confidence:.2%}")

    if is_low_confidence:
        print(f"\n⚠ LOW CONFIDENCE (threshold: {threshold:.0%})")
        print("Please upload a clearer image of the affected leaf.")
    else:
        print(f"\n✓ High confidence prediction")

    print(f"\nTop-{len(top_predictions)} Predictions:")
    for i, pred in enumerate(top_predictions, 1):
        pred_crop = parse_crop_from_class(pred["class"])
        pred_disease = format_disease_name(pred["class"])
        print(f"  {i}. {pred_disease} ({pred['confidence']:.2%})")

    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())