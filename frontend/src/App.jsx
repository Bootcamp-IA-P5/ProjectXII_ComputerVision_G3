import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
    // State Machine: 'UPLOAD' | 'PROCESSING' | 'RESULTS'
    const [viewState, setViewState] = useState('UPLOAD');

    // Data State
    const [file, setFile] = useState(null);
    const [taskId, setTaskId] = useState(null);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    // Parameters
    const [confThreshold, setConfThreshold] = useState(0.25);
    const [iouThreshold, setIouThreshold] = useState(0.45);
    const [fpsSample, setFpsSample] = useState(1);

    // Polling Effect
    useEffect(() => {
        let interval;
        if (viewState === 'PROCESSING' && taskId) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`);
                    if (!response.ok) throw new Error("Error polling task status");

                    const data = await response.json();
                    console.log("Polling Task:", data);

                    if (data.status === 'PROCESSING') {
                        setProgress(data.progress?.percent || 50);
                        setStatusMessage(data.progress?.current_step || "Procesando video...");
                    } else if (data.status === 'SUCCESS') {
                        clearInterval(interval);
                        setProgress(100);
                        setStatusMessage("¡Completado!");
                        // Fetch results immediately
                        fetchResults(data.result.video_id);
                    } else if (data.status === 'FAILURE') {
                        clearInterval(interval);
                        setError(`Error en el procesamiento: ${data.error}`);
                        setViewState('UPLOAD'); // Go back to start on error? Or show error state
                    }
                } catch (err) {
                    console.error("Polling error:", err);
                    // Don't stop polling immediately on one network blip, but maybe log it
                }
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [viewState, taskId]);

    const fetchResults = async (videoId) => {
        try {
            const res = await fetch(`${API_BASE_URL}/videos/${videoId}/results`);
            if (!res.ok) throw new Error("Failed to fetch results");
            const data = await res.json();
            setResults(data);
            setViewState('RESULTS');
        } catch (err) {
            console.error(err);
            setError("No se pudieron cargar los resultados.");
            setViewState('UPLOAD');
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setError(null);
        setViewState('PROCESSING');
        setProgress(0);
        setStatusMessage("Subiendo archivo...");

        const formData = new FormData();
        formData.append('file', file);
        formData.append('confidence_threshold', confThreshold);
        formData.append('iou_threshold', iouThreshold);
        formData.append('fps_sample', fpsSample);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Upload failed: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.task_id) {
                setTaskId(data.task_id);
            } else {
                const taskIdExtract = data.message.match(/Task ID: ([a-f0-9\-]+)/);
                if (taskIdExtract && taskIdExtract[1]) {
                    setTaskId(taskIdExtract[1]);
                } else {
                    throw new Error("Could not retrieve Task ID from response.");
                }
            }

        } catch (err) {
            console.error(err);
            setError(err.message);
            setViewState('UPLOAD');
        }
    };

    const resetApp = () => {
        setFile(null);
        setTaskId(null);
        setResults(null);
        setProgress(0);
        setViewState('UPLOAD');
        setError(null);
    };

    return (
        <div className="min-h-screen bg-[#020617] text-white font-sans selection:bg-primary-500 selection:text-white overflow-x-hidden flex flex-col items-center justify-center">

            {/* Background Ambience */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-900/20 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary-900/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }}></div>
            </div>

            <div className="relative z-10 container mx-auto px-4 py-8 max-w-5xl w-full">

                {/* Header - Centered */}
                <header className="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-6 gap-4">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                        </div>
                        <h1 className="text-2xl font-bold tracking-tight">Project<span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-secondary-400">XII</span> Analysis</h1>
                    </div>
                    <div className="text-sm text-slate-400 font-medium bg-white/5 px-4 py-2 rounded-full backdrop-blur-sm border border-white/10">
                        Backend: {API_BASE_URL.replace('http://', '')} <span className="text-green-400 ml-2">● Online</span>
                    </div>
                </header>

                {/* ERROR TOAST */}
                {error && (
                    <div className="mb-8 p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-200 flex items-center gap-3 animate-bounce max-w-2xl mx-auto">
                        <svg className="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {error}
                    </div>
                )}

                {/* VISTA 1: UPLOAD */}
                {viewState === 'UPLOAD' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-fade-in-up">

                        {/* Main Upload Area */}
                        <div className="lg:col-span-2 space-y-6">
                            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden group hover:border-primary-500/50 transition-colors duration-300">
                                <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-secondary-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>

                                <h2 className="text-xl font-semibold mb-2">Subir Video</h2>
                                <p className="text-slate-400 text-sm mb-8">Arrastra tu archivo aquí o usa el explorador.</p>

                                <label className="flex flex-col items-center justify-center w-full h-80 border-2 border-dashed border-white/20 rounded-2xl cursor-pointer hover:border-primary-400 hover:bg-white/5 transition-all relative z-10">
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        {file ? (
                                            <div className="text-center">
                                                <svg className="w-16 h-16 text-primary-400 mb-4 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                                <p className="text-lg font-medium text-white">{file.name}</p>
                                                <p className="text-sm text-slate-400 mt-1">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                                            </div>
                                        ) : (
                                            <>
                                                <svg className="w-12 h-12 text-slate-500 mb-4 group-hover:text-primary-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                                                <p className="mb-2 text-sm text-slate-400"><span className="font-semibold text-primary-400">Click para subir</span> o arrastra</p>
                                                <p className="text-xs text-slate-600">MP4, AVI, MOV (Max 500MB)</p>
                                            </>
                                        )}
                                    </div>
                                    <input
                                        type="file"
                                        className="hidden"
                                        accept="video/*"
                                        onChange={(e) => setFile(e.target.files[0])}
                                    />
                                </label>
                            </div>
                        </div>

                        {/* Sidebar Params */}
                        <div className="lg:col-span-1 space-y-6">
                            <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md">
                                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                    <svg className="w-5 h-5 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
                                    Parámetros
                                </h3>

                                <div className="space-y-6">
                                    <div>
                                        <div className="flex justify-between mb-2">
                                            <label className="text-sm text-slate-300">Confianza Mínima</label>
                                            <span className="text-sm font-mono text-primary-400">{confThreshold}</span>
                                        </div>
                                        <input type="range" min="0" max="1" step="0.05" value={confThreshold} onChange={(e) => setConfThreshold(e.target.value)} className="w-full accent-primary-500 bg-slate-800 rounded-lg h-2 cursor-pointer" />
                                    </div>

                                    <div>
                                        <div className="flex justify-between mb-2">
                                            <label className="text-sm text-slate-300">IOU Threshold</label>
                                            <span className="text-sm font-mono text-secondary-400">{iouThreshold}</span>
                                        </div>
                                        <input type="range" min="0" max="1" step="0.05" value={iouThreshold} onChange={(e) => setIouThreshold(e.target.value)} className="w-full accent-secondary-500 bg-slate-800 rounded-lg h-2 cursor-pointer" />
                                    </div>

                                    <div>
                                        <div className="flex justify-between mb-2">
                                            <label className="text-sm text-slate-300">FPS Sampling</label>
                                            <span className="text-sm font-mono text-purple-400">1/{fpsSample}</span>
                                        </div>
                                        <div className="flex gap-2">
                                            {[1, 2, 5, 10].map(val => (
                                                <button
                                                    key={val}
                                                    onClick={() => setFpsSample(val)}
                                                    className={`flex-1 py-1 rounded text-xs font-medium transition-all ${fpsSample === val ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/50' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                                                >
                                                    x{val}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={handleUpload}
                                    disabled={!file}
                                    className={`w-full mt-8 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all transform active:scale-95 ${!file ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-gradient-to-r from-primary-600 to-secondary-600 hover:from-primary-500 hover:to-secondary-500 text-white shadow-xl shadow-primary-900/30'}`}
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                                    INICIAR ANÁLISIS
                                </button>
                            </div>
                        </div>
                    </div>
                )}


                {/* VISTA 2: PROGRESS */}
                {viewState === 'PROCESSING' && (
                    <div className="flex flex-col items-center justify-center py-20 animate-fade-in text-center">
                        <div className="relative w-32 h-32 mb-8">
                            <svg className="w-full h-full animate-spin text-slate-800" viewBox="0 0 100 100">
                                <circle className="text-slate-800 stroke-current" strokeWidth="4" cx="50" cy="50" r="40" fill="transparent"></circle>
                                <circle className="text-primary-500 progress-ring__circle stroke-current" strokeWidth="4" strokeLinecap="round" cx="50" cy="50" r="40" fill="transparent" strokeDasharray="251.2" strokeDashoffset={251.2 - (251.2 * progress) / 100}></circle>
                            </svg>
                            {/* Glowing effect holder */}
                            <div className="absolute inset-0 rounded-full border-4 border-primary-500/20 animate-pulse"></div>
                            <div className="absolute inset-0 flex items-center justify-center font-mono text-2xl font-bold text-white">
                                {Math.round(progress)}%
                            </div>
                        </div>

                        <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-secondary-400 mb-2">Analizando Video</h2>
                        <p className="text-slate-400 mb-8 max-w-md mx-auto">{statusMessage || "Iniciando modelos de IA..."}</p>

                        <div className="w-full max-w-md bg-slate-900 rounded-full h-2 mb-12 overflow-hidden shadow-inner">
                            <div className="bg-gradient-to-r from-primary-500 to-secondary-500 h-full transition-all duration-500 ease-out relative" style={{ width: `${progress}%` }}>
                                <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/30 skew-x-12 animate-shimmer"></div>
                            </div>
                        </div>

                        <div className="p-6 bg-white/5 rounded-2xl border border-white/5 max-w-lg w-full">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="w-12 h-16 bg-slate-800 rounded-lg flex items-center justify-center overflow-hidden border border-white/10">
                                    <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                </div>
                                <div className="text-left flex-1">
                                    <h4 className="font-medium text-white">{file?.name || "video.mp4"}</h4>
                                    <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider font-semibold">YOLO11X • PROCESSING</p>
                                </div>
                            </div>
                            <p className="text-xs text-slate-500 text-center">Task ID: <span className="font-mono text-slate-400">{taskId}</span></p>
                        </div>
                    </div>
                )}

                {/* VISTA 3: RESULTS */}
                {viewState === 'RESULTS' && results && (
                    <div className="animate-fade-in-up space-y-8">

                        {/* Result Header */}
                        <div className="flex flex-col md:flex-row gap-6 items-end justify-between">
                            <div>
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-bold uppercase tracking-widest border border-green-500/30 mb-2">
                                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Análisis Completado
                                </div>
                                <h2 className="text-3xl font-bold text-white mb-1">{results.video.filename}</h2>
                                <p className="text-slate-400 text-sm">Duración: {results.video.duration_seconds.toFixed(1)}s • {results.video.total_frames} frames • {results.video.frame_width}x{results.video.frame_height}</p>
                            </div>
                            <div className="flex gap-3">
                                <button onClick={resetApp} className="px-5 py-2.5 rounded-xl bg-slate-800 text-white font-medium hover:bg-slate-700 transition-colors border border-white/10">
                                    Subir otro video
                                </button>
                                <button className="px-5 py-2.5 rounded-xl bg-primary-600 text-white font-medium hover:bg-primary-500 transition-colors shadow-lg shadow-primary-900/50 flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                                    Exportar CSV
                                </button>
                            </div>
                        </div>

                        {/* KPI Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="p-6 rounded-3xl bg-gradient-to-br from-slate-900 to-slate-900 border border-white/10 hover:border-primary-500/30 transition-all group">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-sm font-medium">Detecciones Totales</h3>
                                    <div className="p-2 bg-primary-500/20 rounded-lg text-primary-400 group-hover:scale-110 transition-transform">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                    </div>
                                </div>
                                <p className="text-4xl font-bold text-white mt-2">{results.total_detections}</p>
                                <div className="mt-4 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-primary-500 w-2/3"></div>
                                </div>
                            </div>

                            <div className="p-6 rounded-3xl bg-gradient-to-br from-slate-900 to-slate-900 border border-white/10 hover:border-secondary-500/30 transition-all group">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-sm font-medium">Marcas Únicas</h3>
                                    <div className="p-2 bg-secondary-500/20 rounded-lg text-secondary-400 group-hover:scale-110 transition-transform">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                                    </div>
                                </div>
                                <p className="text-4xl font-bold text-white mt-2">{results.unique_brands}</p>
                                <div className="mt-4 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-secondary-500 w-1/3"></div>
                                </div>
                            </div>

                            <div className="p-6 rounded-3xl bg-gradient-to-br from-slate-900 to-slate-900 border border-white/10 hover:border-purple-500/30 transition-all group">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-sm font-medium">Tiempo de Procesamiento</h3>
                                    <div className="p-2 bg-purple-500/20 rounded-lg text-purple-400 group-hover:scale-110 transition-transform">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                    </div>
                                </div>
                                <p className="text-4xl font-bold text-white mt-2">{results.processing_time_seconds ? results.processing_time_seconds.toFixed(1) : '--'}s</p>
                                <div className="mt-4 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-purple-500 w-full animate-pulse-slow"></div>
                                </div>
                            </div>
                        </div>

                        {/* Top Brands List */}
                        <div className="bg-white/5 border border-white/10 rounded-3xl overflow-hidden backdrop-blur-md">
                            <div className="p-6 border-b border-white/5 flex justify-between items-center">
                                <h3 className="font-semibold text-lg">Top Brands Detectadas</h3>
                                <span className="text-xs font-mono text-slate-500 bg-slate-800 px-2 py-1 rounded">SORTED BY DETECTIONS</span>
                            </div>
                            <div className="p-0">
                                {Object.entries(results.brands)
                                    .sort(([, a], [, b]) => b.detections - a.detections)
                                    .map(([name, brand], index) => (
                                        <div key={name} className="flex items-center justify-between p-6 border-b border-white/5 hover:bg-white/5 transition-colors group">
                                            <div className="flex items-center gap-4">
                                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg ${index === 0 ? 'bg-yellow-500/20 text-yellow-400 ring-1 ring-yellow-500/50' : 'bg-slate-700 text-slate-400'}`}>
                                                    {index + 1}
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-white text-lg">{name}</h4>
                                                    <p className="text-xs text-slate-400">
                                                        <span className="text-primary-400 font-bold">{brand.detections} detections</span> • {brand.screen_time_seconds.toFixed(1)}s screen time
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-8">
                                                <div className="text-right">
                                                    <div className="text-xs text-slate-500 mb-1">CONFIDENCE</div>
                                                    <div className="font-mono text-white text-lg">{(brand.avg_confidence * 100).toFixed(1)}%</div>
                                                </div>

                                                {/* Mini Chart Visualization */}
                                                <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden hidden sm:block">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-primary-600 to-secondary-600"
                                                        style={{ width: `${Math.min(100, (brand.detections / results.total_detections) * 100 * 3)}%` }} // Fake scale factor for visuals
                                                    ></div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        </div>

                    </div>
                )}

            </div>
        </div>
    )
}

export default App
