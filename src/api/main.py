""" 
FastAPI application for video analysis API

Handles:
- Video upload and processing
- Results retrieval
- Brand statistics

¿Qué pasa cuando subes un vídeo?
1. React hace: POST /upload con file + parámetros
2. FastAPI recibe en upload_video()
3. Valida: ¿existe el archivo?
4. Guarda: Escribe archivo en disco
5. Registra: Crea row en tabla "videos"
6. Devuelve: {"video_id": 1, "status": "pending", ...}
7. React recibe JSON y muestra "Vídeo subido"

¿Qué pasa cuando pides resultados?
1. React hace: GET /videos/1/results
2. FastAPI obtiene vídeo de BD
3. Obtiene TODAS las detecciones del vídeo 1
4. Agrupa por marca: {"Nike": [det1, det2], "Adidas": [det3]}
5. Calcula: promedios, screen time, primero/último frame
6. Devuelve: JSON gigante con TODO
7. React muestra gráficos con los datos"""

import logging
from pathlib import Path # Maneja rutas de archivos
from datetime import datetime # Timestamps
from typing import Dict, List # Type hints
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware # CORS para React
from sqlalchemy.orm import Session 

from src.config import API_HOST, API_PORT, ALLOWED_ORIGINS, VIDEO_UPLOAD_DIR, DEVICE
from src.database.init_db import init_db, get_db
# DESCOMENTAR cuando se haga la BBDD y los modelos
# from src.database.models import Video, Detection, Brand, AnalysisSession
from src.api.schemas import (
    VideoUploadRequest,
    VideoResponse,
    VideoResultsResponse,
    UploadResponseSchema,
)

logger = logging.getLogger(__name__)

# CREAR APP (instancia de FastAPI)
app = FastAPI(
    title="ProjectXII Computer Vision API",
    description="Video analysis with logo detection",
    version="1.0.0",
)

# CORS (Para que React pueda hablar con FastAPI)
# CORS = Cross-Origin Resource Sharing
# Sin esto React no puede llamar a FastAPI, es como un firewall que permite/rechaza solicitudes de otros dominios
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Que dominios pueden acceder
    allow_credentials=True,         # Permite cookies/auth
    allow_methods=["*"],            # Get, post, delete...
    allow_headers=["*"]             # Cualquier header
)


# EVENTOS (Startup/Shutdown)
@app.on_event("startup")
async def startup_event():
    """
    Se ejecuta al INICIAR la aplicación
    
    Aquí inicializamos cosas que necesitamos antes de procesar requests

    """
    try:
        logger.info("🚀 Starting API...")
        
        # Crear tablas en BD si no existen
        init_db()
        logger.info("✅ Database initialized")

        # Crear carpeta de uploads si no existe
        VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Upload directories created")

        logger.info("🚀 API started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise



@app.on_event("shutdown")
async def shutdown_event():
    """
    Se ejecuta AL APAGAR la aplicación
    Limpiamos recursos (cierres de conexiones, etc)

    """
    logger.info("🛑 Shutting down API...")
    logger.info("✅ Cleanup completed")

# ENDPOINTS
@app.get("/")
async def root():
    """
    Health check endpoint
        
    Usa para verificar si la API está funcionando
    
    Retorna:
        {"status": "ok", "message": "API running"}
    """
    # Devuelve un diccionario que se convierte automaticamente a JSON
    return {
        "status": "ok",
        "message": "API running",
        "version": "1.0.0"
    }

@app.post("/upload", response_model=UploadResponseSchema)
async def upload_video(
    file: UploadFile = File(...),               # ... significa REQUERIDO
    request: VideoUploadRequest = Depends(),    # Pydantic valida parametro
    db: Session = Depends(get_db)               # inyectada automaticamente
):    
    """
    Upload and process video
    
    Qué hace:
    1. Valida que el archivo exista
    2. Guarda archivo en disco
    3. Crea registro en BD
    4. Devuelve ID del vídeo

    Args:
        file: Archivo vídeo MP4/AVI/MOV
        request: confidence_threshold, iou_threshold, fps_sample
        db: Conexión a BD (inyectada por FastAPI)
        
    Returns:
        UploadResponseSchema con:
        - video_id: ID asignado en BD
        - filename: Nombre del archivo
        - status: "pending" (va a procesarse)
        - message: Mensaje informativo
    """
    from src.services.tasks import process_video_task
    from uuid import uuid4
    
    try: 
        # Paso 1: Validar que el archivo exista y tenga nombre
        if not file or not file.filename:
            logger.warning("⚠️ Upload attempt without file")
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Paso 2: Guardar archivo en disco 
        # Lee contenido del archivo
        contents = await file.read()
        
        # Crear ruta con nombre único para evitar sobrescrituras
        original_name = Path(file.filename)
        unique_filename = f"{uuid4().hex}{original_name.suffix}"
        file_path = VIDEO_UPLOAD_DIR / unique_filename
        
        # Escribe contenido a disco 
        file_path.write_bytes(contents)
        logger.info(f"✅ File saved: {file_path}")
        
        # Paso 3: Crear ID Temporal mientras BD no esté lista
        video_id = str(uuid4())
        
        # Paso 4: Encolar tarea Celery para procesar video
        task = process_video_task.delay(
            video_id=video_id,
            video_path=str(file_path),
            confidence_threshold=request.confidence_threshold,
            iou_threshold=request.iou_threshold,
            fps_sample=request.fps_sample
        )
        logger.info(f"✅ Video processing task queued: {task.id}")

        # Paso 5: Devolver respuesta que FastAPI convierte a JSON
        return UploadResponseSchema(
            video_id=video_id,        # ID generado por BD
            filename=file.filename,
            status="queued",            # Estado inicial
            message=f"Video '{file.filename}' uploaded. Processing started. Task ID: {task.id}"
        )
    
    except HTTPException:
        # Si es error HTTP, propagar
        raise
    
    except Exception as e:
        # Cualquier otro error
        logger.error(f"❌ Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/videos", response_model=list[VideoResponse])
async def list_videos(db: Session = Depends(get_db)):
    """
    List all uploaded videos
    
    Qué hace:
    1. Query a BD: obtiene TODOS los vídeos
    2. Devuelve lista de VideoResponse (JSON)
    
    Returns:
        Lista de VideoResponse:
        [
            {"id": 1, "filename": "video1.mp4", "duration_seconds": 120.5, ...},
            {"id": 2, "filename": "video2.mp4", "duration_seconds": 95.2, ...}
        ]
    """
    try:
        # Query "Dame TODOS los videos de la tabla"
        videos = db.query(Video).all()
        logger.info(f"✅ Retrieved {len(videos)} videos from database")
        
        return videos
    
    except Exception as e:
        logger.error(f"❌ List videos error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list videos")
    
    
@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """
    Get single video metadata

    Qué hace:
    1. Query a BD: obtiene un vídeo específico
    2. Si no existe → error 404
    3. Devuelve VideoResponse (JSON)
    
    Args:
        video_id: ID del vídeo (ej: /videos/1)
        
    Returns:
        VideoResponse con info del vídeo
    """
    try:
        # Query: "Dame el video cuya id == video_id"
        # .filter() = WHERE en SQL
        # .first() = devuelve el 1er registro o None
        video = db.query(Video).filter(Video.id == video_id).first()
        
        # Si no encuentra nada, .first() devuelve None
        if not video:
            logger.warning(f"⚠️ Video {video_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Video with ID {video_id} not found"
            )
        logger.info(f"✅ Retrieved video {video_id}")
        return video
    
    except HTTPException:
        raise # Error HTTP
    except Exception as e:
        logger.error(f"❌ Get video error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video")
        
@app.get("/videos/{video_id}/results", response_model=VideoResultsResponse)
async def get_video_results(video_id: int, db: Session = Depends(get_db)):
    """
    Get complete results including detections and statistics

    LA MÁS COMPLEJA    
    Qué hace:
    1. Obtiene vídeo
    2. Obtiene TODAS las detecciones del vídeo
    3. Agrupa por frame y por marca
    4. Calcula estadísticas
    5. Construye respuesta con TODO
    
    Returns:
        VideoResultsResponse con:
        - video: Metadata del vídeo
        - total_detections: Cantidad total
        - unique_brands: Cuántas marcas diferentes
        - brands: Dict con stats por marca
        - detections_by_frame: Detecciones organizadas por frame
    """
    try:
        # Paso 1: Obtener video
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            logger.warning(f"⚠️ Video {video_id} not found")
            raise HTTPException(status_code=404, detail="Video not found")
      
        # Paso 2: Obtener TODAS las detecciones de este video
        # .join(Brand) = conecta con tabla Brand para obtener nombre
        detections = (
            db.query(Detection)
            .join(Brand)
            .filter(Detection.video_id == video_id)
            .all()
        )
        
        logger.info(f"✅ Retrieved {len(detections)} detections for video {video_id}")
        
        # Paso 3: Agrupar detecciones por frame
        # Resultado: {0: [det1, det2], 1: [det3], ...}
        detections_by_frame: Dict[int, List] = {}
        for det in detections:
            frame_num = det.frame_id or 0   # Si no tiene frame_id, usa 0
            if frame_num not in detections_by_frame:
                detections_by_frame[frame_num] = []
            detections_by_frame[frame_num].append(det)
        
        # Paso 4: Calcular estadísticas por MARCA
        # Resultado: {"Nike": {"count": 50, "avg_confidence": 0.85, ...}, ...}
        brands_stats: Dict = {}
        
        for det in detections:
            brand_name = det.brand.name     # Obtener nombre de la marca relacionada
            
            # Si es la primera vez que vemos esta marca, crear entrada
            if brand_name not in brands_stats:
                brands_stats[brand_name] = {
                    "detections": 0, 
                    "confidences": [],   # Para calcular promedio despues
                    "frames": set(),    # Para contar frames unicos
                }
        
            # Agregar datos
            brands_stats[brand_name]["detections"] += 1
            brands_stats[brand_name]["confidences"].append(det.confidence)
            brands_stats[brand_name]["frames"].add(det.frame_id or 0)
        
        # Paso 5: Procesar estadisticas (calcular promedios, etc)
        brands_final = {}
        for brand_name, stats in brands_stats.items():
            # Calcular confianza promedio
            avg_conf = (
                sum(stats["confidences"]) / len(stats["confidences"])
                if stats["confidences"]
                else 0.0
            )
            
            # Convertir frames set a lista y ordenar
            frames_list = sorted(list(stats["frames"]))
            
            # Calcular screen time
            screen_time_frames = len(frames_list)
            screen_time_seconds = (
                screen_time_frames / video.fps if video.fps > 0 else 0
            )
        
            # Construir respuesta para esta marca
            brands_final[brand_name] = {
                "brand_name": brand_name,
                "detections": stats["detections"],
                "avg_confidence": round(avg_conf, 3),
                "screen_time_frames": screen_time_frames,
                "screen_time_seconds": round(screen_time_seconds, 2),
                "first_frame": frames_list[0] if frames_list else 0,
                "last_frame": frames_list[-1] if frames_list else 0,
            }
        
        # Paso 6: Construir respuesta final
        return VideoResultsResponse(
            video=video,                        # VideoResponse (convertido automaticamente)
            total_detections=len(detections),   
            unique_brands=len(brands_final),
            brands=brands_final,                # Dict con stats por marca
            detections_by_frame=detections_by_frame,
            processing_time_seconds=None,       # Placeholder
            confidence_threshold=0.5,           # PH, obtener de BD despues
            iou_threshold=0.45,
            fps_sample=1 
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get results")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get Celery task status (for frontend progress tracking)
    """
    from src.services.tasks import process_video_task
    
    task = process_video_task.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,  # PENDING, PROCESSING, SUCCESS, FAILURE
        "progress": task.info if task.status == "PROCESSING" else None,
        "result": task.result if task.successful() else None,
        "error": str(task.info) if task.failed() else None
    }

# MAIN
if __name__ == "__main__":
    import uvicorn
    
    # Inicia servidor Uvicorn (servidor ASGI)
    # ASGI >> Asynchronous Server Gateway Interface
    
    uvicorn.run(
        app,                # La aplicación FastAPI
        host=API_HOST,      # Host, escucha en todas las IPs
        port=API_PORT,      # Puerto
        reload=True,        # Reinicia cada vez que cambias codigo (dev mode)
    )
    
    