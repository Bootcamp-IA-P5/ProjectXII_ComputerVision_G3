"""
YOLO Inference wrapper for logo detection
Handles model loading, predictions, and output normalization
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("ultralytics not installed. Run: pip install ultralytics")

from src.config import (
    YOLO_MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    DEVICE,
)

logger = logging.getLogger(__name__)

class YOLOInference:
    """
    Wrapper for YOLO model inference
    
    Handles:
    - Model Loading (PT or ONNX)
    - Predictions on images
    - Device management (GPU/CPU)
    - Output standardization
    """
    
    def __init__(
        self,
        model_path: str = YOLO_MODEL_PATH,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        iou_threshold: float = IOU_THRESHOLD,
        device: str = DEVICE,
    ):
        """
        Initialize YOLO model
        
        Args:
            model_path: Path to YOLO model (.pt or .onnx)
            confidence_threshold: Min confidence for detections (0-1)
            iou_threshold: IoU threshold for NMS (0-1)
            device: Device to use ('cpu', 'cuda', 'auto')
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        self._validate_model_exists()
        self.model = self._load_model()
        self.class_names = self.model.names
        
        logger.info(
            f"YOLO model loaded from {self.model_path} "
            f"on device {self.device}"
        )
        
    def _validate_model_exists(self) -> None:
        """ Check if model file exists"""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self.model_path} "
                f"Please ensure the model file exists."
            )
            
    def _load_model(self) -> YOLO:
        """ Load YOLO model from file"""
        try:
            model = YOLO(str(self.model_path))
            if self.device == "auto":
                model.to("cuda" if self._has_cuda() else "cpu")
            else:
                model.to(self.device)
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
    @staticmethod
    def _has_cuda() -> bool:
        """ Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError: 
            return False
    
    def predict(
        self,
        image: np.ndarray,
        conf: Optional[float] = None,
        iou: Optional[float] = None,
    ) -> Dict:
        """
        Run inference on image
        
        Args:
            image: Input image (BGR numpy array or path string)
            conf: Confidence threshold override
            iou: IoU threshold override
            
        Returns:
            Dictionary with standardized detections:
            {
                "detections": [
                    {
                        "class_id": int,
                        "class_name": str,
                        "confidence": float,
                        "bbox_normalized": [x_center, y_center, width, height],  # 0-1
                        "bbox_pixel": [x1, y1, x2, y2],  # pixel coordinates
                    },
                    ...
                ],
                "image_shape": (height, width),
                "image_path": str or None,
            }
        """
        conf = conf or self.confidence_threshold
        iou = iou or self.iou_threshold
        
        # Handle image input (path or array)
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                raise ValueError(f"Could not read image from {image}")
        
        original_shape = image.shape[:2] 
        
        # Run inference
        results = self.model.predict(
            image, 
            conf=conf,
            iou=iou,
            verbose=False,
        )
        
        # Parse results
        detections = []
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None:
                for i, box in enumerate(result.boxes):
                    # Get coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf_score = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    
                    # Normalize coordinates (0-1)
                    h, w = original_shape
                    x_center_norm = ((x1 + x2) / 2) / w
                    y_center_norm = ((y1 + y2) / 2) / h
                    width_norm = (x2 - x1) / w
                    height_norm = (y2 - y1) / h
                    
                    detection = {
                        "class_id": cls_id, 
                        "class_name": self.class_names.get(cls_id, f"unknown_{cls_id}"),
                        "confidence": conf_score, 
                        "bbox_normalized": [x_center_norm, y_center_norm, width_norm, height_norm],
                        "bbox_pixel": [int(x1), int(y1), int(x2), int(y2)],
                    }
                    detections.append(detection)
        return {
            "detections": detections,
            "image_shape": original_shape,
            "image_path": None,
        }
    
    def get_class_count(self, detections: List[Dict]) -> Dict[str, int]:
        """
        Count detections per class
        
        Args:
            detections: List of detections dicts
            
        Returns:
            Dict mapping class_name -> count
        """
        class_count = {}
        for det in detections:
            class_name = det["class_name"]
            class_count[class_name] = class_count.get(class_name, 0) + 1
        return class_count
    
    def __repr__(self) -> str:
        return (
            f"YOLOInference(model={self.model_path.name}, "
            f"device={self.device}, "
            f"conf_threshold={self.confidence_threshold})"
        )