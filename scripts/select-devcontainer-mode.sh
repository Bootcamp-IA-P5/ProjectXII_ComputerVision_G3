#!/bin/bash
# =============================================================================
# DevContainer Mode Selector Script
# =============================================================================
# This script switches between different devcontainer configurations:
#   - nvidia-gpu: For training with NVIDIA GPU (CUDA image + Python feature)
#   - cpu: For development/production without GPU (MS Python image)
#
# IMPORTANT: Run this script FROM YOUR HOST (Windows/Linux/Mac), NOT inside the container!
#
# Usage:
#   bash scripts/select-devcontainer-mode.sh              # Interactive mode
#   bash scripts/select-devcontainer-mode.sh cpu          # Direct mode
#   bash scripts/select-devcontainer-mode.sh nvidia-gpu   # Direct mode
#
# After running this script:
#   - If container is running: Rebuild it (F1 → Dev Containers: Rebuild Container)
#   - If container is not running: Open it normally in VS Code
# =============================================================================

set -e

# Configuration
DEVCONTAINER_DIR=".devcontainer"
DEST_FILE="$DEVCONTAINER_DIR/devcontainer.json"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display available configurations
list_available() {
    echo -e "${BLUE}Available devcontainer configurations:${NC}"
    echo ""
    
    # Find all devcontainer.* files (excluding .json)
    for file in "$DEVCONTAINER_DIR"/devcontainer.*; do
        if [[ -f "$file" ]]; then
            suffix="${file#$DEVCONTAINER_DIR/devcontainer.}"
            if [[ "$suffix" != "json" ]]; then
                case "$suffix" in
                    "nvidia-gpu")
                        echo -e "  ${GREEN}nvidia-gpu${NC}  - 🎮 Training mode (NVIDIA CUDA, GPU acceleration)"
                        ;;
                    "cpu")
                        echo -e "  ${GREEN}cpu${NC}         - 💻 Development/Production mode (no GPU required)"
                        ;;
                    *)
                        echo -e "  ${GREEN}$suffix${NC}"
                        ;;
                esac
            fi
        fi
    done
    echo ""
}

# Function to display usage information
show_usage() {
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}           DevContainer Mode Selector                          ${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "This script switches between GPU and CPU devcontainer configurations."
    echo ""
    echo -e "${BLUE}Usage:${NC} $0 <mode>"
    echo ""
    list_available
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 nvidia-gpu   # For training YOLO models with NVIDIA GPU"
    echo "  $0 cpu          # For development/production (no GPU needed)"
    echo ""
}

# Function to detect current mode
get_current_mode() {
    if [ -f "$DEST_FILE" ]; then
        if grep -q "NVIDIA GPU Mode" "$DEST_FILE"; then
            echo "nvidia-gpu"
        elif grep -q "CPU Mode" "$DEST_FILE"; then
            echo "cpu"
        else
            echo "unknown"
        fi
    else
        echo "none"
    fi
}

# Detect if running inside container
if [ -f "/.dockerenv" ] || grep -q ":/workspace" /proc/1/cgroup 2>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: You are running this script INSIDE the dev container.${NC}"
    echo -e "${YELLOW}   This will work, but you'll need to rebuild the container manually.${NC}"
    echo ""
    echo -e "${BLUE}Recommended workflow:${NC}"
    echo "   1. Exit the container (close VS Code or stop the container)"
    echo "   2. Run this script from your host machine (Windows/Linux/Mac)"
    echo "   3. Then open the container in VS Code"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    echo ""
fi

# Check if .devcontainer directory exists
if [ ! -d "$DEVCONTAINER_DIR" ]; then
    echo -e "${RED}Error: $DEVCONTAINER_DIR directory not found.${NC}"
    echo "Make sure you're running this script from the project root."
    exit 1
fi

# Check if an argument was provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}           DevContainer Mode Selector                          ${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Available devcontainer configurations:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} cpu         - 💻 Development/Production mode (no GPU required)"
    echo -e "  ${GREEN}[2]${NC} nvidia-gpu  - 🎮 Training mode (NVIDIA CUDA, GPU acceleration)"
    echo ""
    echo -e "${BLUE}Select a configuration:${NC}"
    echo ""
    read -p "Enter your choice (1, cpu, 2, or nvidia-gpu): " user_input
    
    if [ -z "$user_input" ]; then
        echo -e "${RED}No mode selected. Exiting.${NC}"
        exit 1
    fi
    
    # Convert number to mode name
    case "$user_input" in
        1|cpu|CPU)
            MODE="cpu"
            ;;
        2|nvidia-gpu|NVIDIA-GPU|gpu|GPU)
            MODE="nvidia-gpu"
            ;;
        *)
            echo -e "${RED}Invalid choice: $user_input${NC}"
            echo "Please enter: 1, cpu, 2, or nvidia-gpu"
            exit 1
            ;;
    esac
else
    # Normalize the input to lowercase and map aliases to canonical modes
    input_mode=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    case "$input_mode" in
        gpu)
            MODE="nvidia-gpu"
            ;;
        *)
            MODE="$input_mode"
            ;;
    esac
fi
TARGET_FILE="$DEVCONTAINER_DIR/devcontainer.$MODE"

# Get current mode
CURRENT_MODE=$(get_current_mode)

# Check if already in the selected mode
if [ "$CURRENT_MODE" = "$MODE" ]; then
    echo ""
    echo -e "${YELLOW}ℹ️  The devcontainer is already configured for '$MODE' mode.${NC}"
    echo ""
    read -p "Do you want to reapply this configuration anyway? (y/N): " reapply
    if [[ ! "$reapply" =~ ^[Yy]$ ]]; then
        echo "No changes made."
        exit 0
    fi
    echo ""
fi

# Check if the target configuration exists
if [ -f "$TARGET_FILE" ]; then
    # Copy the selected configuration to devcontainer.json
    cp "$TARGET_FILE" "$DEST_FILE"
    
    # Touch the file to update modification time and help VS Code detect the change
    touch "$DEST_FILE"
    
    echo ""
    echo -e "${GREEN}✅ Successfully switched devcontainer configuration:${NC}"
    echo -e "   ${YELLOW}From:${NC} $CURRENT_MODE"
    echo -e "   ${GREEN}To:${NC}   $MODE"
    echo ""
    
    # Show mode-specific information
    case "$MODE" in
        "nvidia-gpu")
            echo -e "${YELLOW}🎮 NVIDIA GPU Mode - Training Configuration${NC}"
            echo ""
            echo "   Purpose: Training YOLO models with GPU acceleration"
            echo ""
            echo "   Configuration:"
            echo "   - Uses Dockerfile with NVIDIA CUDA 12.1 runtime"
            echo "   - Enables all available NVIDIA GPUs (--gpus all)"
            echo "   - Allocates 8GB shared memory for GPU operations"
            echo ""
            echo "   Requirements:"
            echo "   - NVIDIA GPU (RTX, GTX, Quadro, etc.)"
            echo "   - NVIDIA Container Toolkit installed on host"
            echo "   - NVIDIA drivers compatible with CUDA 12.1"
            echo ""
            echo "   Use cases:"
            echo "   - Training YOLO models on local machine"
            echo "   - Running training notebooks (Training_YOLO*.ipynb)"
            echo "   - GPU-accelerated inference for testing"
            ;;
        "cpu")
            echo -e "${YELLOW}💻 CPU Mode - Development/Production Configuration${NC}"
            echo ""
            echo "   Purpose: Development and production without GPU dependency"
            echo ""
            echo "   Configuration:"
            echo "   - Uses Microsoft Python 3.11 base image"
            echo "   - Installs PyTorch CPU-only version (smaller, faster)"
            echo "   - No CUDA or GPU drivers required"
            echo ""
            echo "   Requirements:"
            echo "   - Any machine (no special hardware needed)"
            echo "   - Docker Desktop or Docker Engine"
            echo ""
            echo "   Use cases:"
            echo "   - Running FastAPI backend"
            echo "   - Development and testing"
            echo "   - Production deployment"
            echo "   - Team members without NVIDIA GPU"
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}🔄 Next steps - IMPORTANT:${NC}"
    echo ""
    echo -e "${YELLOW}IF the dev container is currently RUNNING:${NC}"
    echo "   1. Open VS Code"
    echo -e "   2. Press ${GREEN}F1${NC} or ${GREEN}Ctrl+Shift+P${NC}"
    echo -e "   3. Type and select: ${GREEN}Dev Containers: Rebuild Container${NC}"
    echo "   4. Wait for the rebuild to complete"
    echo ""
    echo -e "${YELLOW}IF the dev container is NOT running:${NC}"
    echo "   1. Open VS Code"
    echo -e "   2. Press ${GREEN}F1${NC} or ${GREEN}Ctrl+Shift+P${NC}"
    echo -e "   3. Type and select: ${GREEN}Dev Containers: Reopen in Container${NC}"
    echo "   4. The container will build with the new configuration"
    echo ""
else
    echo -e "${RED}Error: Configuration '$MODE' not found at '$TARGET_FILE'.${NC}"
    echo ""
    list_available
    exit 1
fi
