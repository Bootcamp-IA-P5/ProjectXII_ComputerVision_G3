# DevContainer Configuration Guide

This project uses a **dual-mode devcontainer** system that allows team members to switch between CPU and GPU configurations based on their hardware availability.

## 🎯 Quick Start

### Choose Your Mode

**CPU Mode (Default)**: Works on any machine, no GPU required  
**GPU Mode**: For training with NVIDIA GPU acceleration

### Switch Between Modes

**From your HOST machine** (outside the container):

```bash
# Switch to CPU mode
bash scripts/select-devcontainer-mode.sh cpu

# Switch to GPU mode (requires NVIDIA GPU)
bash scripts/select-devcontainer-mode.sh gpu
# or
bash scripts/select-devcontainer-mode.sh nvidia-gpu
```

**After running the script:**
- If container is running: Rebuild it (`F1` → `Dev Containers: Rebuild Container`)
- If container is not running: Open it normally in VS Code

---

## 💻 CPU Mode

### When to Use
- Development without GPU
- Running FastAPI backend
- Testing and debugging
- Team members without NVIDIA GPU
- Mac users (NVIDIA GPUs not supported on Mac)

### Configuration
- **Base Image**: `mcr.microsoft.com/devcontainers/python:2-3.11-trixie`
- **Python Version**: 3.11
- **PyTorch**: CPU-only version (from `requirements.txt`)
- **Hardware Requirements**: None (works on any machine)

### Features
- ✅ Lightweight image
- ✅ Fast container startup
- ✅ Works on Windows, Linux, and Mac
- ✅ No special drivers needed

---

## 🎮 GPU Mode (NVIDIA)

### When to Use
- Training YOLO models locally
- Running training notebooks (`Training_YOLO*.ipynb`)
- GPU-accelerated inference for testing
- Faster training experiments

### Configuration
- **Base Image**: `nvidia/cuda:12.1.0-runtime-ubuntu22.04`
- **Python Version**: 3.11
- **PyTorch**: CUDA-enabled 2.1.2+cu121 (installed via `postCreateCommand`)
- **GPU Access**: `--gpus all`
- **Shared Memory**: 8GB (for data loading)

### Host Requirements
- **Operating System**: Linux or Windows with WSL2
- **GPU**: NVIDIA GPU (RTX, GTX, Quadro, etc.)
- **NVIDIA Container Toolkit**: Must be installed on host
- **NVIDIA Drivers**: Compatible with CUDA 12.1+

#### Install NVIDIA Container Toolkit (Linux)

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### Install NVIDIA Container Toolkit (Windows WSL2)

Follow: https://docs.nvidia.com/cuda/wsl-user-guide/index.html

### Features
- ✅ Full GPU acceleration
- ✅ CUDA 12.1 runtime
- ✅ Automatic GPU detection
- ✅ Optimized for YOLO training

### Verify GPU Access

After rebuilding the container in GPU mode:

```bash
# Check PyTorch sees GPU
python3 -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# Check NVIDIA driver
nvidia-smi
```

---

## 📊 TensorBoard Visualization

### Convert Training Results to TensorBoard

YOLO training generates CSV files in `runs/detect/*/results.csv`. Convert them to TensorBoard format:

```bash
# Convert a specific training run
python scripts/csv_to_tensorboard.py logo_detection_v1

# Convert all runs
python scripts/csv_to_tensorboard.py --all

# Overwrite existing TensorBoard logs
python scripts/csv_to_tensorboard.py logo_detection_v1 --overwrite
```

### Launch TensorBoard

```bash
# Start TensorBoard server
tensorboard --logdir runs/tensorboard_logs --port 6006
```

Then open in your browser: **http://localhost:6006**

The devcontainer automatically forwards port 6006, so TensorBoard will be accessible from your host machine.

### Available Metrics

TensorBoard will show:
- Training loss
- Validation loss
- Precision, Recall, mAP50, mAP50-95
- Learning rate curves
- Per-class metrics

---

## 🧠 Model Architecture Visualization with Netron

### Why Not TensorBoard for Model Graphs?

**TensorBoard's GRAPHS tab doesn't work with YOLO models** because:
- YOLO uses **dynamic tensor operations** (shapes change based on input)
- PyTorch's `torch.jit.trace()` requires static shapes
- TensorBoard graph export expects traceable operations

Attempting to export YOLO to TensorBoard graphs produces empty event files (88 bytes) with no graph data.

### Solution: Use Netron for ONNX Models

**Netron** (https://netron.app) is a neural network visualizer that supports ONNX, PyTorch, TensorFlow, and many other formats.

#### Export Model to ONNX

First, convert a trained YOLO model to ONNX format:

```python
from ultralytics import YOLO

# Load trained model
model = YOLO("models/trained/yolo11n_logos_best.pt")

# Export to ONNX
model.export(format="onnx")
# Creates: models/trained/yolo11n_logos_best.onnx
```

Or export multiple models:

```bash
python3 << 'EOF'
from ultralytics import YOLO
import os

models_dir = "models/trained"
model_files = [f for f in os.listdir(models_dir) if f.endswith('.pt')]

for model_file in model_files:
    model_path = os.path.join(models_dir, model_file)
    print(f"Exporting {model_file}...")
    model = YOLO(model_path)
    model.export(format="onnx")
    print(f"✅ {model_file.replace('.pt', '.onnx')} created")
EOF
```

#### Visualize with Netron

**Option 1: Web Browser (No Installation)**

1. Go to https://netron.app
2. Click "Open Model" or drag-and-drop your `.onnx` file
3. Explore the model architecture

**Option 2: Desktop App**

```bash
# Install Netron desktop app (optional)
pip install netron

# Launch with a specific model
netron models/trained/yolo11n_logos_best.onnx
```

#### What You Can See in Netron

Netron displays:

- **Layer-by-layer architecture**:
  - Conv2D layers with kernel sizes, strides, padding
  - Batch normalization layers
  - Activation functions (SiLU, ReLU)
  - Pooling layers (MaxPool, AdaptiveAvgPool)
  
- **Tensor shapes at each layer**:
  - Input: `[batch, 3, 640, 640]` (RGB images)
  - Feature maps: `[batch, channels, height, width]`
  - Output: Detection tensors with bounding boxes + class probabilities
  
- **Model structure**:
  - Backbone (CSPDarknet for YOLO11, Darknet for YOLOv8)
  - Neck (PANet/FPN feature pyramid)
  - Head (detection heads at multiple scales)
  
- **Weights and parameters**:
  - Total parameters count
  - Individual layer weights (expandable)
  - Bias values

- **Operators and connections**:
  - Data flow between layers
  - Skip connections (residual blocks)
  - Concatenation operations

#### Example: Viewing YOLO11n Architecture

```bash
# 1. Export model to ONNX
python3 -c "from ultralytics import YOLO; YOLO('models/trained/yolo11n_logos_best.pt').export(format='onnx')"

# 2. Open in browser
# Visit https://netron.app and upload: models/trained/yolo11n_logos_best.onnx
```

You'll see:
- **Input layer**: `images` [1, 3, 640, 640]
- **Backbone**: ~200 Conv2D + BatchNorm + SiLU layers
- **Neck**: Feature pyramid with upsampling + concatenation
- **Output heads**: 3 detection heads at different scales
- **Output tensors**: Bounding boxes, objectness, class probabilities

#### ONNX Model Sizes

Note: ONNX models are large and **excluded from git** (`.gitignore`):

| Model | .pt Size | .onnx Size |
|-------|----------|------------|
| yolo11n | ~5 MB | ~11 MB |
| yolov8n | ~6 MB | ~13 MB |
| yolo11x | ~131 MB | ~273 MB |

Generate ONNX models locally when needed.

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `devcontainer.json` | Active configuration (CPU or GPU) |
| `devcontainer.cpu` | CPU mode template |
| `devcontainer.nvidia-gpu` | GPU mode template |
| `Dockerfile` | Custom CUDA image build (GPU mode) |

**Note**: Do not edit `devcontainer.json` directly. Use the selector script to switch modes.

---

## ⚙️ Environment Variables

Both modes use the same `.env` file (git-ignored):

```bash
# Model inference settings
CONFIDENCE_THRESHOLD=0.25
IOU_THRESHOLD=0.45
DEVICE=auto  # 'auto' detects GPU/CPU, or specify 'cpu'/'cuda:0'

# Roboflow dataset
ROBOFLOW_API_KEY=your_api_key_here
ROBOFLOW_WORKSPACE=your_workspace

# Optional: Slack notifications
SLACK_WEBHOOK_URL=your_webhook_url
```

---

## 📦 Port Forwarding

Both configurations forward these ports automatically:

| Port | Service | Description |
|------|---------|-------------|
| 8000 | FastAPI | Backend API server |
| 3000 | React Dev | Frontend development server |
| 5173 | Vite Dev | Alternative frontend server |
| 6006 | TensorBoard | Training metrics visualization |

---

## 🐛 Troubleshooting

### "GPU not detected" in GPU mode

1. Verify NVIDIA drivers on host: `nvidia-smi`
2. Verify NVIDIA Container Toolkit: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`
3. Check Docker has GPU access: `docker info | grep -i nvidia`
4. Rebuild container: `F1` → `Dev Containers: Rebuild Container`

### "Permission denied" when running selector script

```bash
chmod +x scripts/select-devcontainer-mode.sh
```

### Port already in use

If port 6006 (TensorBoard) or 8000 (FastAPI) is busy:

```bash
# Find process using port
lsof -i :6006

# Kill process
kill -9 <PID>
```

### Python version mismatch

Both CPU and GPU modes use **Python 3.11** for consistency. If you see version conflicts:

```bash
python3 --version  # Should show 3.11.x in both modes
```

---

## 🚀 Workflow Example

### Training with GPU

```bash
# 1. Switch to GPU mode (from host)
bash scripts/select-devcontainer-mode.sh gpu

# 2. Rebuild container in VS Code
# F1 → Dev Containers: Rebuild Container

# 3. Verify GPU
python3 -c "import torch; print(torch.cuda.is_available())"

# 4. Run training notebook
# Open: notebooks/Training_YOLO11x_K.ipynb
# Run all cells

# 5. Convert results to TensorBoard
python scripts/csv_to_tensorboard.py yolo11x_training

# 6. Launch TensorBoard
tensorboard --logdir runs/tensorboard_logs --port 6006
```

### Development with CPU

```bash
# 1. Switch to CPU mode (from host)
bash scripts/select-devcontainer-mode.sh cpu

# 2. Rebuild container
# F1 → Dev Containers: Rebuild Container

# 3. Run API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 4. Test inference
python3 -c "from src.model_inference.yolo_inference import YOLOInference; model = YOLOInference(); print('Model loaded!')"
```

---

## 📚 Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [NVIDIA Container Toolkit Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [TensorBoard Documentation](https://www.tensorflow.org/tensorboard/get_started)
- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)

---

## 🤝 Team Notes

- **Default Mode**: CPU (for maximum compatibility)
- **Mac Users**: Must use CPU mode (NVIDIA GPUs not supported)
- **Dataset**: Download via Roboflow API (see `dataset_yolov8/README.md`)
- **Training Weights**: Excluded from repo (generate locally)
- **TensorBoard Logs**: Regenerate from CSV files (`scripts/csv_to_tensorboard.py`)

For questions or issues, contact the team lead or open an issue on GitHub.
