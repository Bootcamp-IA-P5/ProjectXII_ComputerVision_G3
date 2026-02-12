
import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

def rebalance_dataset(base_dir, split_ratios=(0.7, 0.2, 0.1)):
    """
    Rebalance dataset split.
    
    Args:
        base_dir (str): Base directory containing train, val, test subdirs.
        split_ratios (tuple): (train, val, test) split ratios.
    """
    base_path = Path(base_dir)
    images = []
    
    # Collect all image files
    print("Collecting files...")
    for split in ['train', 'valid', 'test']:
        img_dir = base_path / split / 'images'
        lbl_dir = base_path / split / 'labels'
        
        if not img_dir.exists():
            continue
            
        for img_file in img_dir.glob('*'):
            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                # Find corresponding label
                lbl_file = lbl_dir / (img_file.stem + '.txt')
                if lbl_file.exists():
                    images.append((img_file, lbl_file))
                else:
                    print(f"Warning: Label not found for {img_file}")

    total_images = len(images)
    print(f"Found {total_images} image-label pairs.")
    
    if total_images == 0:
        print("No images found to rebalance.")
        return

    # Shuffle
    random.seed(42) # For reproducibility
    random.shuffle(images)
    
    # Calculate split indices
    n_train = int(total_images * split_ratios[0])
    n_val = int(total_images * split_ratios[1])
    n_test = total_images - n_train - n_val
    
    splits = {
        'train': images[:n_train],
        'valid': images[n_train:n_train+n_val],
        'test': images[n_train+n_val:]
    }
    
    print(f"New split counts: Train={len(splits['train'])}, Val={len(splits['valid'])}, Test={len(splits['test'])}")
    
    # Move files
    print("Moving files...")
    for split_name, file_pairs in splits.items():
        # Ensure target directories exist
        split_img_dir = base_path / split_name / 'images'
        split_lbl_dir = base_path / split_name / 'labels'
        split_img_dir.mkdir(parents=True, exist_ok=True)
        split_lbl_dir.mkdir(parents=True, exist_ok=True)
        
        for img_src, lbl_src in tqdm(file_pairs, desc=f"Moving to {split_name}"):
            # Construct target paths
            img_dst = split_img_dir / img_src.name
            lbl_dst = split_lbl_dir / lbl_src.name
            
            # Move image if not already there
            if img_src != img_dst:
                shutil.move(str(img_src), str(img_dst))
                
            # Move label if not already there
            if lbl_src != lbl_dst:
                shutil.move(str(lbl_src), str(lbl_dst))
                
    print("Rebalance complete!")

if __name__ == "__main__":
    # Correct path relative to where script is run
    DATASET_PATH = r"c:\Users\Coder\OneDrive\Desktop\F5\ProjectXII_ComputerVision_G3\dataset_yolov8\dataset_final_yolo_format_openlogos"
    rebalance_dataset(DATASET_PATH)
