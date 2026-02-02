# 🚀 YOLOv8 Training Environment

Este directorio contiene la configuración Docker para entrenar modelos YOLOv8 con GPU.

## 📋 Requisitos Previos

1. **Docker Desktop** instalado y funcionando
2. **NVIDIA GPU** con drivers actualizados
3. **NVIDIA Container Toolkit** (incluido en Docker Desktop para Windows)

### Verificar que tu GPU funciona con Docker:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## 🏃 Cómo Ejecutar

### 1. Construir la imagen Docker

```bash
cd c:\dev\proyectos\PXII_G3_ComputerVision
docker-compose -f docker/docker-compose.training.yml build
```

> ⏱️ La primera vez tarda ~10-15 minutos descargando dependencias.

### 2. Iniciar el contenedor con Jupyter

```bash
docker-compose -f docker/docker-compose.training.yml up
```

### 3. Abrir Jupyter Lab

Una vez iniciado, abre en tu navegador:
```
http://localhost:8888
```

### 4. Ejecutar el notebook

1. Navega a `notebooks/yolo-training_a.ipynb`
2. Ejecuta las celdas en orden
3. El entrenamiento puede tardar varias horas

## 📁 Estructura de Archivos

```
docker/
├── Dockerfile.training          # Imagen con CUDA + PyTorch + YOLOv8
├── docker-compose.training.yml  # Configuración para ejecutar con GPU
└── README.md                    # Este archivo

notebooks/
└── yolo-training_a.ipynb        # Notebook de entrenamiento

dataset_yolov8/                  # Dataset de logos (ya incluido)
├── train/images/                # ~2232 imágenes
├── valid/images/                # ~402 imágenes
├── test/images/                 # ~670 imágenes
└── data.yaml                    # Configuración del dataset

runs/detect/                     # Resultados del entrenamiento (generado)
└── logo_detection_v1/
    ├── weights/
    │   ├── best.pt              # Mejor modelo
    │   └── last.pt              # Último checkpoint
    ├── results.csv              # Métricas por época
    └── results.png              # Gráficas de entrenamiento

models/                          # Modelos exportados (generado)
├── best.pt                      # Modelo PyTorch
└── best.onnx                    # Modelo ONNX
```

## ⚙️ Configuración para RTX 3050 (4GB)

Los hiperparámetros en el notebook están optimizados para tu GPU:

| Parámetro | Valor | Motivo |
|-----------|-------|--------|
| `MODEL_NAME` | yolov8n.pt | Modelo nano, menor uso de memoria |
| `BATCH_SIZE` | 8 | Máximo recomendado para 4GB VRAM |
| `IMAGE_SIZE` | 640 | Equilibrio entre calidad y memoria |
| `WORKERS` | 4 | Paralelo de carga de datos |

### Si tienes errores de memoria (CUDA OOM):

1. Reduce `BATCH_SIZE` a 4 o 2
2. Reduce `IMAGE_SIZE` a 512 o 416
3. Usa `cache=False` (ya configurado)

## 🛑 Detener el Contenedor

```bash
# En otra terminal:
docker-compose -f docker/docker-compose.training.yml down

# O presiona Ctrl+C en la terminal donde está corriendo
```

## 🔄 Comandos Útiles

```bash
# Ver logs del contenedor
docker-compose -f docker/docker-compose.training.yml logs -f

# Entrar al contenedor con bash
docker-compose -f docker/docker-compose.training.yml exec yolo-training bash

# Verificar uso de GPU dentro del contenedor
docker-compose -f docker/docker-compose.training.yml exec yolo-training nvidia-smi

# Reconstruir imagen (si cambias Dockerfile)
docker-compose -f docker/docker-compose.training.yml build --no-cache
```

## 📊 Métricas Esperadas

Para un dataset de logos con ~175 clases, después de 50 épocas:

- **mAP@0.50**: ~0.70 - 0.85 (objetivo)
- **mAP@0.50-0.95**: ~0.45 - 0.60
- **Precision**: ~0.75 - 0.90
- **Recall**: ~0.65 - 0.80

> Nota: Los resultados varían según la calidad del dataset.

## 🆘 Problemas Comunes

### "CUDA out of memory"
- Reduce `BATCH_SIZE` en el notebook
- Cierra otras aplicaciones que usen GPU

### "No such file or directory: data.yaml"
- Verifica que `dataset_yolov8/data.yaml` existe
- Las rutas en data.yaml deben ser absolutas (`/workspace/...`)

### El contenedor no arranca
```bash
# Verificar que Docker tiene acceso a GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Jupyter no carga
- Espera unos segundos después de `docker-compose up`
- Verifica el log para ver si hay errores
