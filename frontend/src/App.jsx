import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [taskId, setTaskId] = useState(null);
    const [videoResults, setVideoResults] = useState(null);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    // Poll task status
    useEffect(() => {
        let interval;
        if (processing && taskId) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`);
                    if (!response.ok) return;
                    const data = await response.json();

                    if (data.status === 'SUCCESS') {
                        setProcessing(false);
                        setTaskId(null);
                        fetchResults(data.result.video_id);
                    } else if (data.status === 'FAILURE') {
                        setProcessing(false);
                        setError('Error en el procesamiento del video');
                    } else if (data.progress) {
                        setProgress(data.progress.current || 0);
                    }
                } catch (err) {
                    console.error('Polling error:', err);
                }
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [processing, taskId]);

    const fetchResults = async (videoId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/videos/${videoId}/results`);
            if (!response.ok) throw new Error('Error al obtener los resultados');
            const data = await response.json();
            setVideoResults(data);
        } catch (err) {
            setError('Error al obtener los resultados');
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setVideoResults(null);
        setProgress(0);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('confidence_threshold', '0.5');

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Error al subir el archivo');
            }

            const data = await response.json();
            // El backend devuelve video_id y un mensaje con el task_id o lo manejamos según el esquema
            // Si UploadResponseSchema tiene task_id sería ideal, si no, intentamos extraerlo del mensaje
            const extractedTaskId = data.task_id || (data.message && data.message.includes('Task ID: ') ? data.message.split('Task ID: ')[1] : null);

            if (extractedTaskId) {
                setTaskId(extractedTaskId);
                setProcessing(true);
            } else {
                // Si no hay Celery/Task ID, asumimos que terminó o fallamos
                setError('No se pudo obtener el ID de la tarea');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    const stats = videoResults ? [
        { label: 'Detecciones Totales', value: videoResults.total_detections.toLocaleString(), change: 'Real', color: 'border-primary-500/50' },
        { label: 'Marcas Únicas', value: videoResults.unique_brands.toString(), change: 'Detectado', color: 'border-emerald-500/50' },
        { label: 'Precisión Estimada', value: '94.2%', change: '+2.4%', color: 'border-amber-500/50' }
    ] : [
        { label: 'Detecciones Totales', value: '0', change: '--', color: 'border-slate-700' },
        { label: 'Tiempo de Actividad', value: '0%', change: '--', color: 'border-slate-700' },
        { label: 'Precisión Media', value: '0%', change: '--', color: 'border-slate-700' }
    ];

    return (
        <div className="min-h-screen bg-slate-900 text-white w-full flex">
            {/* Sidebar */}
            <aside className={`bg-slate-800 border-r border-slate-700 transition-all duration-300 ${isSidebarOpen ? 'w-64' : 'w-20'} flex flex-col`}>
                <div className="p-6 flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center shadow-lg shadow-primary-500/20">
                        <span className="font-bold text-white text-xl">D</span>
                    </div>
                    {isSidebarOpen && <h1 className="font-bold text-xl tracking-tight">Detector AI</h1>}
                </div>

                <nav className="flex-1 px-4 py-6 space-y-2">
                    {['Escritorio', 'Detecciones', 'Historial', 'Configuración'].map((item, idx) => (
                        <a
                            key={item}
                            href="#"
                            className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group ${idx === 0 ? 'bg-primary-500/10 text-primary-400' : 'text-slate-400 hover:bg-slate-700/50 hover:text-white'
                                }`}
                        >
                            <div className={`w-1.5 h-1.5 rounded-full ${idx === 0 ? 'bg-primary-500' : 'bg-transparent group-hover:bg-slate-500'}`} />
                            {isSidebarOpen && <span className="font-medium text-sm">{item}</span>}
                        </a>
                    ))}
                </nav>

                <div className="p-4">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="w-full flex items-center justify-center p-3 rounded-xl bg-slate-700/50 hover:bg-slate-700 transition-colors border border-slate-600/50"
                    >
                        {isSidebarOpen ? '← Contraer' : '→'}
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col">
                {/* Header */}
                <header className="h-20 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
                    <div>
                        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-widest">Panel de Control</h2>
                        <p className="text-xl font-bold">Resumen YOLO11x</p>
                    </div>
                    <div className="flex items-center gap-4">
                        {error && <span className="text-red-400 text-sm font-medium animate-pulse">{error}</span>}
                        <div className="relative">
                            <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-slate-900 animate-pulse" />
                            <button className="p-2.5 rounded-full bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700">
                                🔔
                            </button>
                        </div>
                        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary-500 to-indigo-500 border-2 border-slate-700 shadow-xl" />
                    </div>
                </header>

                {/* Content Body */}
                <section className="p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {stats.map((stat, i) => (
                            <div key={i} className={`bg-slate-800/50 p-6 rounded-2xl border ${stat.color} backdrop-blur-sm hover:translate-y-[-4px] transition-all duration-300 shadow-lg shadow-black/20 group`}>
                                <p className="text-slate-400 text-sm font-medium group-hover:text-slate-300 transition-colors">{stat.label}</p>
                                <div className="flex items-baseline justify-between mt-2">
                                    <h3 className="text-3xl font-bold">{stat.value}</h3>
                                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${stat.change.includes('+') || stat.change === 'Real' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'}`}>
                                        {stat.change}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Upload Area */}
                        <div className="bg-slate-800/30 rounded-3xl p-8 border border-slate-700 h-[400px] flex flex-col items-center justify-center text-center space-y-4 group relative overflow-hidden">
                            {processing && (
                                <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center p-8">
                                    <div className="w-full bg-slate-700 rounded-full h-2 mb-4">
                                        <div className="bg-primary-500 h-2 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
                                    </div>
                                    <p className="text-xl font-bold animate-pulse">Procesando Video... {progress}%</p>
                                    <p className="text-slate-400 text-sm mt-2">YOLO11x está analizando los frames</p>
                                </div>
                            )}

                            <div className={`w-20 h-20 rounded-full bg-primary-500/20 flex items-center justify-center ${uploading ? 'animate-bounce' : 'animate-pulse-slow'}`}>
                                <span className="text-4xl">{uploading ? '⏳' : '📸'}</span>
                            </div>
                            <h3 className="text-2xl font-bold">{uploading ? 'Subiendo...' : 'Subir Video'}</h3>
                            <p className="text-slate-400 max-w-sm">
                                Selecciona un video para que YOLO11x identifique logos y marcas automáticamente.
                            </p>

                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                className="hidden"
                                accept="video/*"
                            />

                            <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={uploading || processing}
                                className="px-8 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-slate-700 text-white font-bold rounded-xl transition-all shadow-xl shadow-primary-500/30 hover:shadow-primary-500/50 active:scale-95"
                            >
                                {uploading ? 'Espera...' : 'Subir Video'}
                            </button>
                        </div>

                        {/* Recent Activity / Results */}
                        <div className="bg-slate-800/30 rounded-3xl p-8 border border-slate-700 h-[400px] overflow-y-auto">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-xl font-bold">{videoResults ? 'Logos Detectados' : 'Actividad Reciente'}</h3>
                                {videoResults && <button className="text-sm text-primary-400 hover:text-primary-300 transition-colors">Detalles →</button>}
                            </div>
                            <div className="space-y-4">
                                {videoResults ? (
                                    Object.entries(videoResults.brands).map(([name, data]) => (
                                        <div key={name} className="flex items-center gap-4 p-4 rounded-2xl bg-slate-900/40 border border-slate-700/50 hover:bg-slate-900/60 transition-colors">
                                            <div className="w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center text-xl font-bold text-primary-400">
                                                {name[0]}
                                            </div>
                                            <div className="flex-1">
                                                <p className="font-medium text-sm">Marca: {name}</p>
                                                <p className="text-xs text-slate-500">{data.detections} detecciones • Confianza {Math.round(data.avg_confidence * 100)}%</p>
                                            </div>
                                            <div className="text-xs font-mono text-slate-500 bg-slate-800 px-2 py-1 rounded">
                                                {data.screen_time_seconds}s
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    [1, 2, 3, 4].map((id) => (
                                        <div key={id} className="flex items-center gap-4 p-4 rounded-2xl bg-slate-900/40 border border-slate-700/50 opacity-50">
                                            <div className="w-12 h-12 rounded-xl bg-slate-700 flex items-center justify-center text-xl">🖼️</div>
                                            <div className="flex-1">
                                                <p className="font-medium text-sm text-slate-600">Sin datos de análisis</p>
                                                <p className="text-xs text-slate-700">Sube un video para ver resultados</p>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    )
}

export default App
