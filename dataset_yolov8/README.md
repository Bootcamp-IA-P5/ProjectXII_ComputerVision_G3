# Dataset YOLOv8 - Logo Detection

Este directorio contiene la configuración del dataset para detección de logos usando YOLOv8/YOLO11.

## 📥 Descargar el Dataset

El dataset **NO** está incluido en el repositorio para mantener el tamaño del repo manejable.

### Opción 1: Roboflow (Recomendado)
Descarga el dataset desde Roboflow Universe:

```bash
# URL del dataset
https://universe.roboflow.com/sekant/my-first-project-4wl7u/dataset/1

# Formato: YOLOv8
# Licencia: CC BY 4.0
```

### Opción 2: Descarga directa (si disponible)
Si el equipo tiene una URL de descarga directa, úsala aquí:

```bash
# Descargar y descomprimir
wget <URL_DEL_DATASET> -O dataset_yolov8.zip
unzip dataset_yolov8.zip -d dataset_yolov8/
```

## 📁 Estructura del Dataset

Después de descargar, la estructura debe ser:

```
dataset_yolov8/
├── data.yaml                # Configuración del dataset (incluido en repo)
├── data_local_v11x.yaml    # Configuración local alternativa
├── README.dataset.txt      # Info del dataset
├── README.roboflow.txt     # Info de Roboflow
├── train/
│   ├── images/             # Imágenes de entrenamiento
│   └── labels/             # Anotaciones de entrenamiento
├── valid/
│   ├── images/             # Imágenes de validación
│   └── labels/             # Anotaciones de validación
└── test/
    ├── images/             # Imágenes de test
    └── labels/             # Anotaciones de test
```

## 📊 Estadísticas del Dataset

- **Total de imágenes**: 3,304
  - Train: 2,232 imágenes
  - Valid: 402 imágenes
  - Test: 670 imágenes
- **Clases (logos)**: 175
- **Tamaño aproximado**: ~56 MB

## 🏆 Top 15 Logos más frecuentes

1. **Outlook** (195 imágenes)
2. **PayPal** (155 imágenes)
3. **Chase Personal Banking** (100 imágenes)
4. **Bank of America** (93 imágenes)
5. **Facebook** (56 imágenes)
6. **Adobe** (56 imágenes)
7. **DHL** (52 imágenes)
8. **Amazon** (50 imágenes)
9. **Netflix** (45 imágenes)
10. **Dropbox** (44 imágenes)
11. **Apple** (41 imágenes)
12. **eBay** (40 imágenes)
13. **Alibaba** (39 imágenes)
14. **Deutsche Telekom** (35 imágenes)
15. **Google** (35 imágenes)

## ⚙️ Configuración

El archivo [`data.yaml`](data.yaml) contiene:
- Rutas a las imágenes de train/valid/test
- Número de clases (175)
- Nombres de todas las clases
- Metadatos de Roboflow

**Importante**: Las rutas en `data.yaml` están configuradas para funcionar dentro del contenedor Docker.

## 🐳 Uso con Docker

Si estás usando Docker (recomendado), el dataset debe estar en:
```
/workspace/dataset_yolov8/
```

El volumen se monta automáticamente según el `docker-compose.yml`.

## 📝 Verificar Dataset

Para verificar que el dataset se descargó correctamente:

```bash
# Desde la raíz del proyecto
python scripts/analyze_dataset_logos.py
```

Este script mostrará:
- Número de imágenes por split (train/valid/test)
- Distribución de logos
- Estadísticas detalladas

## 🚫 Ignorado en Git

Las siguientes carpetas/archivos están ignorados en `.gitignore`:
- `dataset_yolov8/train/images/`
- `dataset_yolov8/train/labels/`
- `dataset_yolov8/valid/images/`
- `dataset_yolov8/valid/labels/`
- `dataset_yolov8/test/images/`
- `dataset_yolov8/test/labels/`

Solo se incluyen:
- ✅ `data.yaml` (configuración)
- ✅ Este `README.md`
- ✅ Estructura de carpetas (`.gitkeep`)

## 📚 Documentación Adicional

- Ver análisis completo de logos: `scripts/analyze_dataset_logos.py`
- Ver prompts para generación de videos: `examples/sora_prompts_logos.txt`
- Notebooks de entrenamiento: `notebooks/`
