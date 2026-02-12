
import sys
import os
import asyncio
from pathlib import Path
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from src.database.models import Video, Detection, VideoBrandStats, Brand
from src.video_processor.video_processor import VideoProcessor
from src.model_inference.yolo_inference import YOLOInference
from src.config import DATABASE_URL, YOLO_MODEL_PATH
from src.database.repository import DetectionRepository

async def verify_inference():
    print("🚀 Starting End-to-End Inference Verification")
    
    # 1. Setup paths
    video_path = Path("videos/Video3_MasterCard.mp4")
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📂 Video file found: {video_path}")
    print(f"🧠 Model path: {YOLO_MODEL_PATH}")
    
    # 2. Initialize database connection
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in environment")
        return
        
    engine = create_engine(DATABASE_URL)
    session = Session(engine)
    repo = DetectionRepository(session)
    
    print("✅ Database connected")

    # 3. Process video
    print("running inference... (this may take a moment)")
    
    try:
        # Initialize YOLO inference
        inference = YOLOInference(str(YOLO_MODEL_PATH))
        
        # Initialize processor
        processor = VideoProcessor(inference, fps_sample=1)
        
        # Run processing
        print(f"🎬 Processing video: {video_path}")
        
        # Run full processing pipeline
        results = processor.process_video(
            str(video_path),
            save_to_db=False # We will save manually to verify repository
        )
        
        if "error" in results:
            print(f"❌ Processing failed: {results['error']}")
            return

        print(f"📸 Processed {results['processed_frames']} frames")
        print(f"🔍 Inference complete. Detected {results['statistics']['total_detections']} objects")
        
        print(f"🔍 Inference complete. Detected {results['statistics']['total_detections']} objects")
        
        # 4. Save to Database
        print("💾 Saving results to Supabase...")
        saved_video = repo.save_video_result(results)
        video_id = saved_video.id
        
        print(f"✅ Results saved. Video ID: {video_id}")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Verify Database Records
    print("\n🔍 Verifying Database Records:")
    
    # Check Video
    video = session.query(Video).filter(Video.id == video_id).first()
    print(f"  - Video Record: {'✅ Found' if video else '❌ Missing'}")
    if video:
        print(f"    • Filename: {video.filename}")
        print(f"    • Processed Frames: {video.processed_frames}")
    
    # Check Detections
    detection_count = session.query(func.count(Detection.id)).filter(Detection.video_id == video_id).scalar()
    print(f"  - Total Detections: {detection_count} {'✅' if detection_count > 0 else '⚠️'}")
    
    # Check Stats
    stats = session.query(VideoBrandStats).filter(VideoBrandStats.video_id == video_id).all()
    print(f"  - Brand Stats Records: {len(stats)} {'✅' if len(stats) > 0 else '⚠️'}")
    
    if len(stats) > 0:
        print("\n🏆 Top Detected Brands:")
        for stat in stats:
            brand_name = session.query(Brand.name).filter(Brand.id == stat.brand_id).scalar()
            print(f"    • {brand_name}: {stat.detection_count} detections, {stat.screen_time_seconds:.2f}s screen time")

    session.close()

if __name__ == "__main__":
    asyncio.run(verify_inference())
