"""
Detection Pipeline - Core orchestrator for video analysis
Integrates YOLOInference and VideoProcessor for end-to-end detection workflow
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.model_inference import YOLOInference
from src.video_processor import VideoProcessor
from src.config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD

logger = logging.getLogger(__name__)


class DetectionPipeline:
    """ 
    Complete detection pipeline for video analysis
    
    Orchestrates:
    - Model initialization and inference
    - Video loading and frame extraction
    - Detection processing and aggregation
    - Results export and reporting    
    """
    
    def __init__(
        self, 
        model_path: str = YOLO_MODEL_PATH,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        iou_threshold: float = IOU_THRESHOLD, 
        fps_sample: int = 1,
    ):
        """
        Initialize Detection Pipeline
        
        Args:
            model_path: Path to YOLO model (.pt or .onnx)
            confidence_threshold: Min confidence for detections (0-1)
            iou_threshold: IoU threshold for NMS (0-1)
            fps_sample: Extract 1 frame every N frames (1 = every frame)
        """
        logger.info("Initializing DetectionPipeline...")
        
        # Initialize YOLO model
        self.yolo = YOLOInference(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )
        
        # Initialize video processor
        self.processor = VideoProcessor(
            model=self.yolo,
            fps_sample=fps_sample,
        )
        
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.fps_sample = fps_sample
        self.last_results = None
        
        logger.info("DetectionPipeline initialized successfully")
        
    def process_video(
        self,
        video_path: str,
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        save_results: bool = False, 
        output_dir: Optional[str] = None,
    ) -> Dict:
        """
        Orquesta: Carga video > Extrae frames > procesa > agrega stats
        
        Complete video processing pipeline
        
        Args:
            video_path: Path to video file
            conf: confidence threshold override
            iou: IoU threshold override
            save_results: Save results to JSON file
            output_dir: Directory to save results (if save_results=True)
            
        Returns: 
            Complete results dictionary with detections and statitstics
        """
        logger.info(f"Starting pipeline for video: {video_path}")
        
        try:
            # Process video through pipeline
            results = self.processor.process_video(
                video_path=video_path,
                conf=conf,
                iou=iou,
            )
            
            # Handle errors from processor
            if "error" in results:
                logger.error(f"Pipeline error: {results['error']}")
                return results
            
            # Enhance results with pipeline metadata 
            results["pipeline_metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "confidence_threshold": conf or self.confidence_threshold,
                "iou_threshold": iou or self.iou_threshold,
                "fps_sample": self.fps_sample,
            }
            
            # Store for later retrieval
            self.last_results = results
            
            # Save results if requested
            if save_results:
                self._save_results(results, output_dir)
                
            logger.info("Pipeline processing completed successfully")
            return results
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return {"error": f"Pipeline failed: {str(e)}"}
        
    def get_summary(self, results: Optional[Dict] = None) -> Dict:
        """
        Resumen legible: "Nike 150 detections, 5 seconds screen time"
        
        Generate human-readable summary from results
        
        Args:
            results: Results dict (uses last_results if None)
        
        Returns: 
            Summary dictionary with key metrics    
        """
        results = results or self.last_results
        
        if not results or "error" in results:
            return {"error": "No valid results available"}
        
        stats = results.get("statistics", {})
        
        summary = {
            "video": Path(results["video_path"]).name,
            "duration_seconds": round(results["duration_seconds"], 2),
            "total_frames": results["total_frames"],
            "processed_frames": results["processed_frames"],
            "fps": round(results["fps"], 2),
            "total_detections": stats.get("total_detections", 0),
            "unique_brands": stats.get("unique_classes", 0),
            "brands": {}
        }
        
        # Add per-brand summary
        for brand_name, brand_stats in stats.get("by_class", {}).items():
            summary["brands"][brand_name] = {
                "detections": brand_stats["count"],
                "avg_confidence": round(brand_stats["avg_confidence"], 3),
                "screen_time_frames": brand_stats["screen_time_frames"],
                "screen_time_seconds": round(
                    brand_stats["screen_time_frames"] / results["fps"], 2
                ) if results["fps"] > 0 else 0,
                "first_frame": brand_stats["first_frame"],
                "last_frame": brand_stats["last_frame"],
            }
        
        # Sort brands by detection count (descending)
        summary["brands"] = dict(
            sorted(
                summary["brands"].items(),
                key=lambda x: x[1]["detections"],
                reverse=True
            )
        )
        
        return summary
    def _save_results(self, results: Dict, output_dir: Optional[str] = None) -> None:
        """
        Guarda resultados en JSON
        
        Save results to JSON file
        
        Args:
            results: Results dictionary
            output_dir: Output directory (uses default if None)
        """
        try:
            import json
            
            if output_dir is None:
                from src.config import DATA_DIR
                output_dir = DATA_DIR / "detections"
                
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            video_name = Path(results["video_path"]).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"{video_name}_{timestamp}_detections.json"
            
            # Save results (skip numpy/non-serializable objects)
            serializable_results = {
                "video_path": results["video_path"],
                "total_frames": results["total_frames"],
                "processed_frames": results["processed_frames"],
                "fps": results["fps"],
                "duration_seconds": results["duration_seconds"],
                "frame_dimensions": results["frame_dimensions"],
                "statistics": results["statistics"],
                "pipeline_metadata": results.get("pipeline_metadata", {}),
            }
            
            with open(output_file, "w") as f:
                json.dump(serializable_results, f, indent=2)
                
            logger.info(f"Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def get_brand_timeline(self, results: Optional[Dict] = None) -> Dict[str, List[int]]:
        """ 
        Dice en qué frames aparece cada marca
        
        Get frame indices where each brand appears
        Args: 
            results: results dict (uses last_results if None)
            
        Returns:
            Dict mapping brand_name -> List of frame indices
        """
        results = results or self.last_results
        
        if not results or "error" in results:
            return {}
        
        timeline = {}
        detections_by_frame = results.get("detections_by_frame", {})
        
        for frame_idx, detections in detections_by_frame.items():
            for det in detections:
                brand = det["class_name"]
                if brand not in timeline:
                    timeline[brand] = []
                timeline[brand].append(frame_idx)
        
        # Sort frame indices for each brand
        for brand in timeline:
            timeline[brand] = sorted(set(timeline[brand]))
        
        return timeline
    
    def close(self) -> None:
        """Cleanup resources"""
        self.processor.close()
        logger.info("DetectionPipeline closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        
    def __repr__(self) -> str:
        return (
            f"DetectionPipeline("
            f"conf_threshold={self.confidence_threshold}, "
            f"iou_threshold={self.iou_threshold}, "
            f"fps_sample={self.fps_sample})"
        )