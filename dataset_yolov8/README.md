# Dataset YOLOv8 - Logo Detection

This directory contains the dataset configuration for logo detection using YOLOv8/YOLO11.

## 📥 Download the Dataset

The dataset is **NOT** included in the repository to keep the repo size manageable.

### Option 1: Roboflow (Recommended)
Download the dataset from Roboflow Universe:

```bash
# Dataset URL
https://universe.roboflow.com/sekant/my-first-project-4wl7u/dataset/1

# Format: YOLOv8
# License: CC BY 4.0
```

### Option 2: Direct Download (if available)
If the team has a direct download URL, use it here:

```bash
# Download and extract
wget <DATASET_URL> -O dataset_yolov8.zip
unzip dataset_yolov8.zip -d dataset_yolov8/
```

## 📁 Dataset Structure

After downloading, the structure should be:

```
dataset_yolov8/
├── data.yaml                # Dataset configuration (included in repo)
├── README.dataset.txt      # Dataset info
├── README.roboflow.txt     # Roboflow info
├── train/
│   ├── images/             # Training images
│   └── labels/             # Training annotations
├── valid/
│   ├── images/             # Validation images
│   └── labels/             # Validation annotations
└── test/
    ├── images/             # Test images
    └── labels/             # Test annotations
```

## 📊 Dataset Statistics

- **Total images**: 3,304
  - Train: 2,232 images
  - Valid: 402 images
  - Test: 670 images
- **Classes (logos)**: 175
- **Approximate size**: depends on Roboflow export; check exact size when downloading.

## 🏆 Top 15 Most Frequent Logos

1. **Outlook** (195 images)
2. **PayPal** (155 images)
3. **Chase Personal Banking** (100 images)
4. **Bank of America** (93 images)
5. **Facebook** (56 images)
6. **Adobe** (56 images)
7. **DHL** (52 images)
8. **Amazon** (50 images)
9. **Netflix** (45 images)
10. **Dropbox** (44 images)
11. **Apple** (41 images)
12. **eBay** (40 images)
13. **Alibaba** (39 images)
14. **Deutsche Telekom** (35 images)
15. **Google** (35 images)

## ⚙️ Configuration

The [`data.yaml`](data.yaml) file contains:
- Paths to train/valid/test images
- Number of classes (175)
- Names of all classes
- Roboflow metadata

**Important**: Paths in `data.yaml` are configured to work inside the Docker container.

## 🐳 Usage with Docker

If using Docker (recommended), the dataset should be located at:
```
/workspace/dataset_yolov8/
```

The volume is automatically mounted according to `docker-compose.yml`.

## 📝 Verify Dataset

To verify the dataset was downloaded correctly:

```bash
# From the project root
python scripts/analyze_dataset_logos.py
```

This script will display:
- Number of images per split (train/valid/test)
- Logo distribution
- Detailed statistics

## 🚫 Ignored in Git

The following folders/files are ignored in `.gitignore`:
- `dataset_yolov8/train/images/`
- `dataset_yolov8/train/labels/`
- `dataset_yolov8/valid/images/`
- `dataset_yolov8/valid/labels/`
- `dataset_yolov8/test/images/`
- `dataset_yolov8/test/labels/`

Only included:
- ✅ `data.yaml` (configuration)
- ✅ This `README.md`
- ✅ Folder structure (`.gitkeep`)

## 📚 Additional Documentation

- See complete logo analysis: `scripts/analyze_dataset_logos.py`
- See prompts for video generation: `examples/sora_prompts_logos.txt`
- Training notebooks: `notebooks/`
