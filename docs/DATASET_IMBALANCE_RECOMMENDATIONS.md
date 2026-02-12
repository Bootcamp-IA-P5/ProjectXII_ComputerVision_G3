# 📊 Dataset Class Imbalance Analysis & Recommendations

This document analyzes the class imbalance in the logo detection dataset and provides actionable recommendations for improving model performance on underrepresented brands.

## Current Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Images** | 3,304 |
| **Total Classes** | 175 |
| **Avg Images/Class** | ~19 |
| **Max Images (Outlook)** | 195 |
| **Estimated Min Images** | <10 |

### Class Distribution (Top 15 vs Long Tail)

```
Outlook         ████████████████████ 195
PayPal          ████████████████ 155
Chase           ██████████ 100
Bank of America █████████ 93
Facebook        ██████ 56
Adobe           ██████ 56
DHL             █████ 52
Amazon          █████ 50
Netflix         ████ 45
Dropbox         ████ 44
Apple           ████ 41
eBay            ████ 40
Alibaba         ████ 39
Deutsche Telekom ███ 35
Google          ███ 35
...
[160 other classes with fewer samples]
```

## Impact of Class Imbalance

### 1. Detection Performance
- **Well-represented classes** (50+ images): Generally high precision and recall
- **Under-represented classes** (<20 images): Lower recall, model may fail to detect them
- **Rare classes** (<10 images): High risk of complete detection failure

### 2. Model Bias
The model is biased toward predicting common classes (Outlook, PayPal, Chase), potentially:
- Missing rare brand logos entirely
- Misclassifying rare logos as similar common logos

---

## Recommendations

### 1. Data Augmentation (Quick Win)

Apply aggressive augmentation to underrepresented classes during training:

```python
# Albumentations configuration for logo augmentation
import albumentations as A

augmentation = A.Compose([
    # Geometric transforms
    A.HorizontalFlip(p=0.3),
    A.Rotate(limit=15, p=0.3),
    A.Affine(scale=(0.8, 1.2), translate_percent=0.1, p=0.3),
    
    # Color transforms
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.3),
    A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, p=0.2),
    
    # Blur and noise
    A.GaussNoise(var_limit=(10, 50), p=0.1),
    A.MotionBlur(blur_limit=3, p=0.1),
    
    # Background variation
    A.CoarseDropout(max_holes=8, max_height=32, max_width=32, p=0.2),
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
```

### 2. Class Weights in Loss Function

Modify training to weight underrepresented classes higher:

```python
from ultralytics import YOLO
import numpy as np

# Calculate class weights (inverse frequency)
class_counts = {...}  # {class_id: count}
total_samples = sum(class_counts.values())
class_weights = {
    cls: total_samples / (len(class_counts) * count)
    for cls, count in class_counts.items()
}

# Cap weights to avoid extreme values
max_weight = 10.0
class_weights = {k: min(v, max_weight) for k, v in class_weights.items()}

# Train with class weights
model = YOLO('yolo11x.pt')
model.train(
    data='data.yaml',
    epochs=100,
    cls=1.0,  # Classification loss weight
    # Note: YOLO v8/11 doesn't natively support per-class weights
    # Consider using focal loss instead
)
```

### 3. Focal Loss (Recommended for Severe Imbalance)

Focal loss down-weights easy examples (common classes) and focuses on hard examples:

```python
# In ultralytics, you can set:
model.train(
    data='data.yaml',
    fl_gamma=1.5,  # Focal loss gamma (0 = no focal loss, higher = more focus on hard examples)
)
```

### 4. Oversampling Strategy

Create a balanced training set by oversampling rare classes:

```python
import random
from pathlib import Path
import shutil

def create_balanced_dataset(source_dir, target_dir, target_count=100):
    """
    Create a balanced dataset by oversampling rare classes
    """
    for class_name in class_names:
        class_images = list((source_dir / class_name).glob("*.jpg"))
        current_count = len(class_images)
        
        if current_count < target_count:
            # Oversample with repetition
            samples = random.choices(class_images, k=target_count)
        else:
            # Undersample
            samples = random.sample(class_images, k=target_count)
        
        for i, img_path in enumerate(samples):
            shutil.copy(img_path, target_dir / f"{class_name}_{i}.jpg")
```

### 5. Collect More Data for Rare Classes

**Priority classes to collect more data for:**
- Any class with fewer than 20 images
- Classes that are important for the business use case

**Data collection strategies:**
1. **Web scraping**: Search for brand logos on Google Images, brand websites
2. **Synthetic generation**: Use logo on various backgrounds
3. **Video extraction**: Extract frames from brand advertisements

### 6. Synthetic Data Generation

Generate synthetic training data by compositing logos onto varied backgrounds:

```python
import cv2
import numpy as np
from PIL import Image

def generate_synthetic_sample(logo_path, background_path, output_path):
    """
    Composite logo onto random background with transformations
    """
    logo = Image.open(logo_path).convert("RGBA")
    background = Image.open(background_path).convert("RGB")
    
    # Random resize logo
    scale = random.uniform(0.1, 0.4)
    new_size = (int(logo.width * scale), int(logo.height * scale))
    logo = logo.resize(new_size, Image.LANCZOS)
    
    # Random position
    max_x = background.width - logo.width
    max_y = background.height - logo.height
    x = random.randint(0, max(0, max_x))
    y = random.randint(0, max(0, max_y))
    
    # Random rotation
    angle = random.uniform(-15, 15)
    logo = logo.rotate(angle, expand=True)
    
    # Composite
    background.paste(logo, (x, y), logo)
    background.save(output_path)
    
    # Return YOLO annotation
    cx = (x + logo.width / 2) / background.width
    cy = (y + logo.height / 2) / background.height
    w = logo.width / background.width
    h = logo.height / background.height
    
    return f"{class_id} {cx} {cy} {w} {h}"
```

---

## Recommended Training Configuration

Based on the class imbalance, use these training settings:

```yaml
# config/training_balanced.yaml
model: yolo11x.pt
data: dataset_yolov8/data.yaml
epochs: 150
batch: 16
imgsz: 640

# Augmentation (increase for imbalanced data)
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 10
translate: 0.1
scale: 0.5
shear: 5
flipud: 0.0
fliplr: 0.5
mosaic: 1.0
mixup: 0.15
copy_paste: 0.3

# Focal loss for class imbalance
fl_gamma: 1.5

# Patience for early stopping
patience: 30
```

---

## Evaluation Metrics to Track

When dealing with imbalanced data, track these additional metrics:

1. **Per-class mAP**: Monitor mAP for each class, not just overall
2. **Per-class Recall**: Critical for detecting rare logos
3. **Confusion Matrix**: Identify which rare classes get confused with common ones
4. **Tail Class Performance**: Average performance on classes with <20 samples

```python
# After training, analyze per-class performance
from ultralytics import YOLO

model = YOLO('runs/detect/train/weights/best.pt')
metrics = model.val()

# Per-class AP
for i, ap in enumerate(metrics.box.ap50):
    class_name = model.names[i]
    print(f"{class_name}: AP@50 = {ap:.3f}")
```

---

## Action Items

| Priority | Action | Effort | Expected Impact |
|----------|--------|--------|-----------------|
| 🔴 High | Enable focal loss (fl_gamma=1.5) | Low | Moderate |
| 🔴 High | Increase augmentation for rare classes | Medium | High |
| 🟡 Medium | Generate synthetic data for classes <20 images | High | High |
| 🟡 Medium | Implement per-class mAP monitoring | Low | Visibility |
| 🟢 Low | Collect more real data for rare classes | High | Highest |

---

## Appendix: Script to Analyze Dataset

```python
# scripts/analyze_class_balance.py
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt

def analyze_dataset(labels_dir: Path):
    """Analyze class distribution in YOLO format dataset"""
    class_counts = Counter()
    
    for label_file in labels_dir.glob("*.txt"):
        with open(label_file) as f:
            for line in f:
                class_id = int(line.split()[0])
                class_counts[class_id] += 1
    
    # Plot distribution
    plt.figure(figsize=(14, 6))
    counts = sorted(class_counts.values(), reverse=True)
    plt.bar(range(len(counts)), counts)
    plt.xlabel("Class Rank")
    plt.ylabel("Number of Instances")
    plt.title("Class Distribution (Sorted)")
    plt.axhline(y=20, color='r', linestyle='--', label='Minimum Recommended')
    plt.legend()
    plt.savefig("class_distribution.png")
    
    # Report statistics
    print(f"Total classes: {len(class_counts)}")
    print(f"Total instances: {sum(class_counts.values())}")
    print(f"Max instances: {max(class_counts.values())}")
    print(f"Min instances: {min(class_counts.values())}")
    print(f"Classes with <20 instances: {sum(1 for c in class_counts.values() if c < 20)}")
    
    return class_counts

if __name__ == "__main__":
    analyze_dataset(Path("dataset_yolov8/train/labels"))
```
