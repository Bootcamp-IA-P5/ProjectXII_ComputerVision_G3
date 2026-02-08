#!/usr/bin/env python3
"""
Convert YOLO training CSV results to TensorBoard format.

This script reads the results.csv files from YOLO training runs and creates
TensorBoard event files, allowing visualization of historical training data.

Usage:
    python scripts/csv_to_tensorboard.py                    # Convert all runs
    python scripts/csv_to_tensorboard.py logo_detection_v1  # Convert specific run
    python scripts/csv_to_tensorboard.py --list             # List available runs
"""

import argparse
import csv
from pathlib import Path
from torch.utils.tensorboard import SummaryWriter


def get_runs_dir() -> Path:
    """Get the runs/detect directory path."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root / "runs" / "detect"


def list_available_runs() -> list[str]:
    """List all runs that have results.csv files."""
    runs_dir = get_runs_dir()
    runs = []
    
    if not runs_dir.exists():
        return runs
    
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir() and (run_dir / "results.csv").exists():
            runs.append(run_dir.name)
    
    return sorted(runs)


def csv_to_tensorboard(run_name: str, overwrite: bool = False) -> bool:
    """
    Convert a single run's CSV to TensorBoard format.
    
    Args:
        run_name: Name of the run directory
        overwrite: If True, overwrite existing TensorBoard logs
        
    Returns:
        True if conversion was successful, False otherwise
    """
    runs_dir = get_runs_dir()
    run_dir = runs_dir / run_name
    csv_path = run_dir / "results.csv"
    tb_dir = run_dir / "tensorboard_logs"
    
    if not csv_path.exists():
        print(f"  ❌ No results.csv found in {run_name}")
        return False
    
    # Check if TensorBoard logs already exist
    if tb_dir.exists():
        if not overwrite:
            print(f"  ⏭️  TensorBoard logs already exist for {run_name} (use --overwrite)")
            return True
        else:
            # Remove existing directory to avoid merged/duplicated scalars
            import shutil
            shutil.rmtree(tb_dir)
            print(f"  🗑️  Removed existing TensorBoard logs for clean overwrite")
    
    print(f"  📊 Converting {run_name}...")
    
    # Read CSV and write to TensorBoard
    writer = SummaryWriter(log_dir=str(tb_dir))
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Get epoch (handle whitespace in column names)
            epoch = None
            for key in row.keys():
                if 'epoch' in key.lower():
                    epoch = int(float(row[key].strip()))
                    break
            
            if epoch is None:
                continue
            
            # Write all metrics to TensorBoard
            for key, value in row.items():
                key = key.strip()
                if key.lower() == 'epoch' or key.lower() == 'time':
                    continue
                
                try:
                    val = float(value.strip())
                    # Clean up metric name
                    tag = key.replace('(B)', '').strip()
                    writer.add_scalar(tag, val, epoch)
                except (ValueError, AttributeError):
                    continue
    
    writer.close()
    print(f"  ✅ {run_name} converted successfully")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert YOLO CSV results to TensorBoard format"
    )
    parser.add_argument(
        "runs",
        nargs="*",
        help="Specific run names to convert (default: all)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available runs"
    )
    parser.add_argument(
        "--overwrite", "-o",
        action="store_true",
        help="Overwrite existing TensorBoard logs"
    )
    
    args = parser.parse_args()
    
    available_runs = list_available_runs()
    
    if args.list:
        print("\n📁 Available runs with results.csv:")
        print("=" * 40)
        for run in available_runs:
            print(f"  • {run}")
        print(f"\nTotal: {len(available_runs)} runs")
        return
    
    if not available_runs:
        print("❌ No runs found with results.csv")
        return
    
    # Determine which runs to convert
    runs_to_convert = args.runs if args.runs else available_runs
    
    # Validate run names
    invalid_runs = [r for r in runs_to_convert if r not in available_runs]
    if invalid_runs:
        print(f"❌ Invalid runs: {', '.join(invalid_runs)}")
        print(f"   Available: {', '.join(available_runs)}")
        return
    
    print("\n🔄 Converting CSV to TensorBoard format")
    print("=" * 50)
    
    success_count = 0
    for run_name in runs_to_convert:
        if csv_to_tensorboard(run_name, args.overwrite):
            success_count += 1
    
    print("=" * 50)
    print(f"✅ Converted {success_count}/{len(runs_to_convert)} runs")
    print(f"\n🚀 Launch TensorBoard with:")
    print(f"   tensorboard --logdir=runs/detect --port=6006")
    print(f"\n   Then open: http://localhost:6006")


if __name__ == "__main__":
    main()
