# AgroVision AI - ML Pipeline Documentation

## Overview

This directory contains the complete Machine Learning pipeline for crop disease detection using MobileNetV2 fine-tuned on crop leaf images.

## Directory Structure

```
ml/
├── dataset/
│   ├── train/
│   │   ├── Tomato___Healthy/
│   │   ├── Tomato___Early_Blight/
│   │   └── ...
│   ├── validation/
│   │   ├── Tomato___Healthy/
│   │   └── ...
│   └── test/
│       ├── Tomato___Healthy/
│       └── ...
├── models/
│   └── crop_disease_mobilenetv2.pth
├── results/
│   ├── confusion_matrix.png
│   ├── confusion_matrix_raw.png
│   └── evaluation_results.json
├── class_names.json
├── preprocessing.py
├── model.py
├── train.py
├── evaluate.py
└── predict.py
```

## Dataset Preparation

### Folder Structure

Place your dataset in `ml/dataset/` with the following structure:

```
ml/dataset/
├── train/
│   ├── Class_Name_1/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   ├── Class_Name_2/
│   └── ...
├── validation/
│   ├── Class_Name_1/
│   └── ...
└── test/
    ├── Class_Name_1/
    └── ...
```

### Class Naming Convention

Use the format: `Crop___Disease_Name` (triple underscore separator)

Examples:
- `Tomato___Healthy`
- `Tomato___Early_Blight`
- `Tomato___Late_Blight`
- `Potato___Early_Blight`
- `Potato___Late_Blight`
- `Potato___Healthy`
- `Wheat___Stripe_Rust`
- `Rice___Bacterial_Leaf_Blight`

The system automatically detects class names from folder names.

## Installation

### Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### ML Dependencies (if running separately)

```bash
pip install torch torchvision numpy scikit-learn matplotlib seaborn pillow
```

## Training

### Basic Training

```bash
cd ml
python train.py
```

### Custom Training Parameters

```bash
python train.py \
  --data ml/dataset \
  --model-out ml/models/crop_disease_mobilenetv2.pth \
  --class-names ml/class_names.json \
  --epochs 50 \
  --batch-size 32 \
  --lr 1e-3 \
  --fine-tune-lr 1e-4 \
  --freeze-epochs 5 \
  --fine-tune-epochs 15 \
  --patience 10 \
  --workers 4 \
  --image-size 224 \
  --device auto
```

### Training Phases

1. **Phase 1 - Classifier Training** (backbone frozen):
   - Trains only the custom classification head
   - Default: 5 epochs at LR=1e-3
   - Uses AdamW optimizer with ReduceLROnPlateau scheduler

2. **Phase 2 - Fine-tuning** (backbone unfrozen):
   - Unfreezes last 7 layers of MobileNetV2 backbone
   - Default: 15 epochs at LR=1e-4 (backbone) and 1e-3 (classifier)
   - Uses CosineAnnealingLR scheduler

### Early Stopping

Training stops early if validation loss doesn't improve for `patience` epochs (default: 10).

### Outputs

- `ml/models/crop_disease_mobilenetv2.pth` - Best model checkpoint
- `ml/class_names.json` - Class names list
- Training history logged to console

## Evaluation

### Run Evaluation

```bash
cd ml
python evaluate.py
```

### Custom Evaluation Parameters

```bash
python evaluate.py \
  --model ml/models/crop_disease_mobilenetv2.pth \
  --class-names ml/class_names.json \
  --data ml/dataset \
  --batch-size 32 \
  --workers 4 \
  --image-size 224 \
  --device auto \
  --output-dir ml/results
```

### Outputs

- `ml/results/confusion_matrix.png` - Normalized confusion matrix heatmap
- `ml/results/confusion_matrix_raw.png` - Raw count confusion matrix
- `ml/results/evaluation_results.json` - Detailed metrics

### Metrics Reported

- Overall Accuracy
- Macro Precision, Recall, F1-Score
- Per-class Precision, Recall, F1-Score, Support

## Single Image Prediction

### Predict on a Single Image

```bash
cd ml
python predict.py path/to/leaf_image.jpg
```

### Custom Prediction Parameters

```bash
python predict.py path/to/leaf_image.jpg \
  --model ml/models/crop_disease_mobilenetv2.pth \
  --class-names ml/class_names.json \
  --top-k 3 \
  --threshold 0.60 \
  --device auto
```

### Output Format

```
==================================================
PREDICTION RESULT
==================================================
Crop:       Tomato
Disease:    Tomato Early Blight
Confidence: 94.70%

✓ High confidence prediction

Top-3 Predictions:
  1. Tomato Early Blight (94.70%)
  2. Tomato Late Blight (3.20%)
  3. Tomato Healthy (2.10%)
==================================================
```

### Low Confidence Handling

If confidence < threshold (default 60%), a warning is displayed:

```
⚠ LOW CONFIDENCE (threshold: 60%)
Please upload a clearer image of the affected leaf.
```

## FastAPI Integration

### Start Backend Server

```bash
cd backend
python main.py
```

Server runs at `http://localhost:8000` with API docs at `http://localhost:8000/docs`

### API Endpoint

**POST /api/predict**

Upload a leaf image for disease classification.

#### Request

- `image` (file): Leaf image (JPG, JPEG, PNG, WEBP, max 10MB)
- `crop` (form, optional): Target crop type hint

#### Response

```json
{
  "id": "uuid",
  "crop": "Tomato",
  "disease": "Tomato Early Blight",
  "confidence": 94.7,
  "status": "Diseased",
  "symptoms": "Dark brown spots surrounded by yellow rings...",
  "cause": "Fungus (Alternaria solani)",
  "prevention": "Rotate crops every season...",
  "treatment": "Apply copper-based fungicide...",
  "image_url": "/uploads/abc123_leaf.jpg",
  "created_at": "2026-01-15T10:30:00Z",
  "is_temporary_model": false,
  "model_notice": "MobileNetV2 Crop Disease Detection",
  "top_predictions": [
    {"disease": "Tomato Early Blight", "confidence": 94.7},
    {"disease": "Tomato Late Blight", "confidence": 3.2},
    {"disease": "Tomato Healthy", "confidence": 2.1}
  ],
  "low_confidence_warning": false
}
```

### Health Check

**GET /api/health**

```json
{
  "status": "ok",
  "service": "AgroVision AI Backend",
  "version": "1.0.0",
  "supabase_connected": true,
  "environment": "development",
  "model_loaded": true,
  "model_classes": 15
}
```

## Model Architecture

- **Backbone**: MobileNetV2 (ImageNet pretrained)
- **Input**: 224x224 RGB images
- **Preprocessing**: ImageNet normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
- **Head**: Dropout(0.2) → Linear(num_classes)
- **Training**: Two-phase (frozen backbone → fine-tune last 7 layers)

## Preprocessing Details

### Training Augmentation

- Resize to 256x256
- RandomResizedCrop to 224x224 (scale 0.8-1.0)
- RandomHorizontalFlip (p=0.5)
- RandomRotation (±15°)
- ColorJitter (brightness, contrast, saturation, hue)
- ToTensor + ImageNet Normalization

### Validation/Test Preprocessing

- Resize to 224x224
- ToTensor + ImageNet Normalization

## Troubleshooting

### Dataset Not Found

```
Error: Training directory not found: ml/dataset/train
```

Solution: Create the dataset folder structure and add images.

### No Classes Detected

```
Error: No class directories found in ml/dataset/train
```

Solution: Ensure class subdirectories exist under train/ with images.

### Model Not Found

```
Error: Model file not found: ml/models/crop_disease_mobilenetv2.pth
```

Solution: Run training first: `python train.py`

### CUDA Out of Memory

Reduce batch size:
```bash
python train.py --batch-size 16
```

### Class Imbalance

The training uses standard CrossEntropyLoss. For severe imbalance, consider:
- Weighted loss
- Oversampling minority classes
- Focal loss

## Adding New Classes

1. Add new class folders to `ml/dataset/train/`, `validation/`, `test/`
2. Retrain the model: `python train.py`
3. The new classes will be automatically detected and added to `class_names.json`
4. Restart the FastAPI backend to reload the updated model

## Performance Notes

- Model loads once at FastAPI startup (not per request)
- Inference runs on GPU if available, otherwise CPU
- Typical inference time: ~50-100ms per image on GPU
- Batch inference supported for multiple images

## License

Part of AgroVision AI project.