# Backend ↔ Database Contract

## Cómo se conectan backend y database

### 1. Analysis Service retorna dict
El archivo `analysis_service.py` procesa videos y retorna un dict con esta estructura.

### 2. Database team convierte dict → modelos ORM
El archivo `tasks.py` usa los modelos ORM de database team para guardar ese dict en BD.

### 3. Ejemplo real

**Input a `analyze_video()`:**
- video_id: "123e4567-e89b-12d3-a456-426614174000"
- video_path: "./data/uploads/videos/mi_video.mp4"

**Output (dict que retorna):**
```json
{
  "video_id": "123e4567-e89b-12d3-a456-426614174000",
  "success": true,
  "metadata": {
    "fps": 30.0,
    "duration_seconds": 120.5,
    "total_frames": 3615,
    "frame_width": 1920,
    "frame_height": 1080
  },
  "detections_by_frame": {
    "0": [
      {
        "class_id": 5,
        "class_name": "Nike",
        "confidence": 0.92,
        "bbox_pixel": [500, 300, 700, 600],
        "bbox_normalized": [0.5, 0.3, 0.2, 0.4]
      }
    ],
    "15": [...]
  },
  "statistics": {
    "total_detections": 250,
    "unique_classes": 12,
    "by_class": {
      "Nike": {
        "count": 50,
        "avg_confidence": 0.88,
        "frames_with_detection": [0, 1, 2, 5],
        "screen_time_frames": 45,
        "first_frame": 0,
        "last_frame": 150
      }
    }
  }
}