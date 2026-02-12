# 🚀 MLOps & Model Registry Recommendations

This document outlines recommendations for improving the machine learning operations (MLOps) practices for the logo detection project, including experiment tracking, model versioning, and automated pipelines.

## Current State

| Area | Current Status | Target |
|------|---------------|--------|
| **Experiment Tracking** | ❌ Manual notebooks | Automated tracking |
| **Model Versioning** | ❌ Google Drive | Centralized registry |
| **Training Pipelines** | ❌ Manual Colab | Automated CI/CD |
| **Model Serving** | ⚠️ Local files | Versioned deployment |
| **Monitoring** | ❌ None | Performance dashboards |

---

## 1. Experiment Tracking

### Problem
Training experiments are run in Jupyter notebooks without centralized tracking of:
- Hyperparameters
- Metrics (mAP, loss curves)
- Training data version
- Model artifacts

### Solution: MLflow or Weights & Biases

#### Option A: MLflow (Self-hosted, Free)

```python
# notebooks/train_with_mlflow.py
import mlflow
from ultralytics import YOLO

# Set tracking server
mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("logo-detection")

with mlflow.start_run(run_name="yolo11x-v2"):
    # Log parameters
    mlflow.log_params({
        "model": "yolo11x",
        "epochs": 100,
        "batch_size": 16,
        "confidence_threshold": 0.5,
        "iou_threshold": 0.45,
        "dataset_version": "v1.0",
    })
    
    # Train
    model = YOLO("yolo11x.pt")
    results = model.train(
        data="data.yaml",
        epochs=100,
        batch=16,
    )
    
    # Log metrics
    mlflow.log_metrics({
        "mAP50": results.results_dict["metrics/mAP50(B)"],
        "mAP50-95": results.results_dict["metrics/mAP50-95(B)"],
        "precision": results.results_dict["metrics/precision(B)"],
        "recall": results.results_dict["metrics/recall(B)"],
    })
    
    # Log model artifact
    mlflow.log_artifact("runs/detect/train/weights/best.pt")
    
    # Register model
    mlflow.pytorch.log_model(
        model,
        "model",
        registered_model_name="logo-detector"
    )
```

**Docker Compose Addition:**
```yaml
services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    container_name: mlflow
    ports:
      - "5000:5000"
    volumes:
      - mlflow_data:/mlruns
    command: mlflow server --host 0.0.0.0 --backend-store-uri sqlite:///mlflow.db --artifacts-destination /mlruns
```

#### Option B: Weights & Biases (Cloud-hosted)

```python
import wandb
from ultralytics import YOLO

# Initialize W&B
wandb.init(
    project="logo-detection",
    name="yolo11x-training",
    config={
        "model": "yolo11x",
        "epochs": 100,
        "dataset": "roboflow-logos-v1",
    }
)

# YOLO has built-in W&B integration
model = YOLO("yolo11x.pt")
model.train(
    data="data.yaml",
    epochs=100,
    project="wandb-logs",  # Enables W&B logging
)
```

---

## 2. Model Registry

### Problem
- Models stored in Google Drive (manual, no versioning)
- No clear production vs. staging models
- No rollback capability

### Solution: Centralized Model Registry

#### Option A: MLflow Model Registry

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# List all versions of a model
for version in client.search_model_versions("name='logo-detector'"):
    print(f"Version {version.version}: {version.current_stage}")

# Promote model to production
client.transition_model_version_stage(
    name="logo-detector",
    version="3",
    stage="Production"
)

# In application, load production model:
model_uri = "models:/logo-detector/Production"
model = mlflow.pytorch.load_model(model_uri)
```

#### Option B: DVC (Data Version Control) + S3/GCS

```yaml
# .dvc/config
[core]
remote = s3storage

['remote "s3storage"']
url = s3://projectxii-models/
```

```bash
# Track model with DVC
dvc add models/trained/best_yolo11x.pt

# Push to remote storage
dvc push

# Pull specific version
git checkout v1.2.0
dvc pull
```

---

## 3. Automated Training Pipeline

### Problem
Training is manually triggered in Colab/local notebooks, making it:
- Non-reproducible
- Time-consuming
- Error-prone

### Solution: GitHub Actions for Training

```yaml
# .github/workflows/train.yml
name: Model Training

on:
  workflow_dispatch:
    inputs:
      model:
        description: 'Model to train'
        required: true
        default: 'yolo11x'
        type: choice
        options:
          - yolo11x
          - yolov8x
          - yolov8n
      epochs:
        description: 'Number of epochs'
        required: true
        default: '100'

jobs:
  train:
    runs-on: [self-hosted, gpu]  # Requires self-hosted runner with GPU
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Download dataset
        run: |
          pip install roboflow
          python scripts/download_dataset.py
      
      - name: Train model
        env:
          WANDB_API_KEY: ${{ secrets.WANDB_API_KEY }}
        run: |
          python scripts/train.py \
            --model ${{ inputs.model }} \
            --epochs ${{ inputs.epochs }}
      
      - name: Upload model artifact
        uses: actions/upload-artifact@v4
        with:
          name: trained-model
          path: runs/detect/train/weights/best.pt
      
      - name: Register model (if metrics pass)
        run: python scripts/register_model.py
```

---

## 4. Model Serving Updates

### Current Config
```python
# src/config.py
YOLO_MODEL_PATH = MODELS_DIR / "trained" / "best_yolov8x_Kiru.pt"
```

### Recommended: Dynamic Model Loading

```python
# src/config.py
import os

def get_model_path():
    """Get model path from registry or local fallback"""
    
    # Priority 1: MLflow Model Registry
    if os.getenv("MLFLOW_TRACKING_URI"):
        return "models:/logo-detector/Production"
    
    # Priority 2: Environment variable
    if os.getenv("YOLO_MODEL_PATH"):
        return os.getenv("YOLO_MODEL_PATH")
    
    # Priority 3: Local default
    return MODELS_DIR / "trained" / "best_yolo11x.pt"

YOLO_MODEL_PATH = get_model_path()
```

```python
# src/model_inference/yolo_inference.py
def _load_model(self) -> YOLO:
    """Load model from path or MLflow registry"""
    model_path = str(self.model_path)
    
    if model_path.startswith("models:/"):
        # Load from MLflow
        import mlflow
        model = mlflow.pytorch.load_model(model_path)
    else:
        # Load from local file
        model = YOLO(model_path)
    
    return model
```

---

## 5. Model Performance Monitoring

### Metrics to Track in Production

```python
# src/services/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
INFERENCE_LATENCY = Histogram(
    'inference_latency_seconds',
    'Time spent on model inference',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

DETECTION_COUNT = Counter(
    'detection_count_total',
    'Total number of detections',
    ['brand']
)

CONFIDENCE_DISTRIBUTION = Histogram(
    'detection_confidence',
    'Distribution of detection confidences',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# Use in inference
def predict_with_monitoring(self, image):
    start = time.time()
    result = self.model.predict(image)
    INFERENCE_LATENCY.observe(time.time() - start)
    
    for det in result["detections"]:
        DETECTION_COUNT.labels(brand=det["class_name"]).inc()
        CONFIDENCE_DISTRIBUTION.observe(det["confidence"])
    
    return result
```

**Grafana Dashboard:**
```yaml
# docker-compose additions
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

---

## 6. A/B Testing for Model Updates

```python
# src/model_inference/ab_testing.py
import random
from typing import Dict

class ModelABTest:
    def __init__(self, model_a, model_b, traffic_split: float = 0.1):
        """
        A/B test between two models
        
        Args:
            model_a: Current production model (control)
            model_b: New model to test (treatment)
            traffic_split: Fraction of traffic to route to model_b
        """
        self.model_a = model_a
        self.model_b = model_b
        self.traffic_split = traffic_split
    
    def predict(self, image) -> Dict:
        if random.random() < self.traffic_split:
            result = self.model_b.predict(image)
            result["model_variant"] = "B"
        else:
            result = self.model_a.predict(image)
            result["model_variant"] = "A"
        
        return result
```

---

## Implementation Roadmap

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1** | 1 week | MLflow/W&B integration, experiment tracking |
| **Phase 2** | 1 week | Model registry setup, versioning |
| **Phase 3** | 2 weeks | CI/CD training pipeline (GitHub Actions) |
| **Phase 4** | 1 week | Production monitoring, Prometheus/Grafana |
| **Phase 5** | 1 week | A/B testing framework |

---

## Recommended Architecture

```mermaid
flowchart TB
    subgraph Training["Training Pipeline"]
        Data[Dataset v1.0] --> Train[Training Job]
        Train --> MLflow[MLflow Tracking]
        Train --> Artifacts[Model Artifacts]
    end
    
    subgraph Registry["Model Registry"]
        Artifacts --> Registry[MLflow Registry]
        Registry --> Staging[Staging]
        Staging --> Production[Production]
    end
    
    subgraph Serving["Model Serving"]
        Production --> API[FastAPI]
        API --> Prometheus[Prometheus]
        Prometheus --> Grafana[Grafana]
    end
    
    subgraph CICD["CI/CD"]
        GitHub[GitHub Actions] --> Train
        GitHub --> Deploy[Deploy to API]
    end
```

---

## Quick Wins (Immediate Actions)

1. **Add W&B to training notebooks** (~1 hour)
   ```python
   import wandb
   wandb.init(project="logo-detection")
   ```

2. **Create `models/CHANGELOG.md`** (~30 min)
   - Document each model version, training date, metrics

3. **Add model version to API response** (~15 min)
   ```python
   return {
       "detections": [...],
       "model_version": "yolo11x-v2.0",
   }
   ```
