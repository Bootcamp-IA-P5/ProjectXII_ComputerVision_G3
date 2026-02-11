# ProjectXII - Detección de Logos de Marca en Video
## 📋 Descripción del Proyecto
**ProjectXII** es una solución integral de visión por computadora diseñada para automatizar el análisis de presencia de marca en contenido audiovisual. El sistema combina un frontend moderno y reactivo con una arquitectura backend asíncrona potente para procesar videos de alta resolución, detectar logos utilizando modelos **YOLO11x** de última generación y analizar métricas detalladas como el tiempo en pantalla, frecuencia de aparición y confianza.
Nuestra visión es transformar la auditoría de medios publicitarios, pasando de procesos manuales lentos a un flujo de trabajo impulsado por IA que ofrece resultados precisos y escalables en minutos.
## 🎯 Características Principales
*   **Detección Masiva**: Capacidad para identificar **175 clases de marcas** diferentes en un solo pase.
*   **Motor de Inferencia SOTA**: Utiliza **YOLO11x (Extra Large)** optimizado para máxima precisión (mAP).
*   **Arquitectura Asíncrona**: Sistema de colas distribuido con **Celery y Redis** que permite el procesamiento en segundo plano sin bloquear al usuario.
*   **Experiencia de Usuario Premium**: Interfaz "Space Theme" con flujo guiado de 3 pasos (Subida ➔ Progreso en Tiempo Real ➔ Resultados Interactivos).
*   **Visualización de Datos**: Dashboard con cálculo automático de *Screen Time* y ranking de *Top Brands*.
*   **API REST Robusta**: Endpoints documentados y tipados con FastAPI y Pydantic.
## 🚀 Resultados del Modelo
### 📊 Métricas de Rendimiento
El modelo base ha sido entrenado y validado con un dataset extenso de logotipos, alcanzando hitos significativos de rendimiento:
| Métrica | Valor | Estado |
| :--- | :--- | :--- |
| **mAP50** | ~95.9% | ✅ Alta precisión en detección de objetos |
| **Velocidad** | 120ms/frame | ✅ Optimizado para GPU (CUDA) |
| **Recall** | >92% | ✅ Baja tasa de falsos negativos |
### 🔍 Capacidades de Detección
El sistema clasifica logotipos en tiempo real, calculando métricas clave para cada aparición:
1.  **Confidence Score**: Nivel de certeza de la IA (0-100%).
2.  **Bounding Box**: Coordenadas exactas del logo en pantalla.
3.  **Screen Time**: Cuantificación precisa de la exposición de la marca.
## 🛠️ Instalación y Configuración
### Prerrequisitos
*   **Python 3.11+**
*   **React** (para el Frontend)
*   **Redis Server** (Broker de mensajería)
*   **Docker** (Opcional, recomendado para despliegue)
### Instalación Manual
**1. Clonar el repositorio**
```bash
git clone [https://github.com/Bootcamp-IA-P5/ProjectXII_ComputerVision_G3.git](https://github.com/Bootcamp-IA-P5/ProjectXII_ComputerVision_G3.git)
cd ProjectXII_ComputerVision_G3
2. Configurar Backend (API + Worker)

bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
# Instalar dependencias
pip install -r requirements.txt
# Iniciar Redis (en otra terminal)
redis-server
# Iniciar API
export PYTHONPATH=$PYTHONPATH:$(pwd)
python src/api/main.py
# Iniciar Worker (en otra terminal)
export PYTHONPATH=$PYTHONPATH:$(pwd)
celery -A src.services.tasks worker --loglevel=info
3. Configurar Frontend

bash
cd frontend
npm install
npm run dev
🏗️ Estructura del Proyecto
plaintext
ProjectXII_ComputerVision_G3/
├── src/
│   ├── api/                 # Endpoints FastAPI (Upload, Results)
│   ├── services/            # Lógica de negocio y Tareas Celery
│   ├── model_inference/     # Wrapper de Ultralytics YOLO
│   ├── video_processor/     # Procesamiento de video con OpenCV
│   └── database/            # Modelos SQLAlchemy y conexión DB
├── frontend/                # Aplicación React + Vite + Tailwind
│   ├── src/components/      # Componentes UI (Upload, Progress, Dashboard)
│   └── tailwind.config.js   # Configuración del tema "Space"
├── models/                  # Pesos del modelo (.pt)
├── docker/                  # Configuración de contenedores
└── tests/                   # Pruebas unitarias e integración
🚀 Uso del Sistema
1. Subida de Video

Arrastra tu archivo .mp4 o .mov a la zona de carga.
Ajusta los parámetros de inferencia (Umbral de confianza, IoU) si es necesario.
2. Procesamiento (Backend)

El sistema genera un task_id único y encola el trabajo en Celery.
El frontend consulta (poling) el estado cada 2 segundos, mostrando una barra de progreso real sincronizada con el backend.
3. Análisis de Resultados Una vez finalizado, accederás al Dashboard de Resultados:

KPIs: Total de detecciones, marcas únicas encontradas.
Top Brands: Gráfico de barras con las marcas más prevalentes.
Tabla de Detalles: Lista desglosada con confianza promedio y tiempo en pantalla.
📊 Dataset y Entrenamiento
Clases: 175 Logotipos comerciales.
Formato: YOLO v8/v11 (Ultralytics).
Augmentation: Mosaic, Mixup y variaciones de brillo para robustez en condiciones de iluminación variable.
🔧 Desarrollo y Contribución
Ramas Principales
main: Producción estable.
dev: Desarrollo e integración continua.
feature/*: Nuevas características (ej. feature/basic_frontend).
Flujo de Trabajo
Hacer Fork del proyecto.
Crear rama para tu feature (git checkout -b feature/AmazingFeature).
Commit de tus cambios (git commit -m 'Add AmazingFeature').
Push a la rama (git push origin feature/AmazingFeature).
Abrir un Pull Request a dev.
📄 Licencia
Este proyecto es propiedad del equipo G3 de ProjectXII.

👥 Equipo
Rol	Colaborador
Developer	[Aroa Mateo Gómez]
Product Owner	[Ignacio Castillo]
Developer	[Alfonso Bermúdez]
Scrum Master	[Kirutasu Sánchez]
