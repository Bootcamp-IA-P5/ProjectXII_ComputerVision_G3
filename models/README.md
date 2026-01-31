# 📂 Trained Models Weights

This directory is intended to store the trained weights for the logo detection system. 

Due to storage limits on GitHub and to avoid bandwidth issues, the large model weights (`.pt` files) are **not included** in this repository.

### 🚀 Available Models
- **YOLOv11x (Extra Large)**: Best accuracy (mAP50: 0.9703).
- **YOLOv11n (Nano)**: Balanced speed/accuracy.
- **YOLOv8n (Nano)**: Baseline model.

### 📥 Accessing the Weights
For team members: The weights are stored in our shared Google Drive folder.
1. Download the required `.pt` file (e.g., `yolo11x_logos_best.pt`).
2. Place the file inside this `models/` directory.
3. The system is configured to load them from this path by default.

*External users: Please contact the repository owners for access to the model weights.*
