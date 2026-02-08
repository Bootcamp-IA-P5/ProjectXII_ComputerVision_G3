import React, { useState, useRef } from 'react';
import { UploadCloud, FileVideo, Video, AlertCircle, Loader2 } from 'lucide-react';
import { uploadVideo } from '../services/api';
import { useNavigate } from 'react-router-dom';
import styles from './VideoUploader.module.css';

const VideoUploader = () => {
    const navigate = useNavigate();
    const fileInputRef = useRef(null);

    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);

    const [config, setConfig] = useState({
        confidence: 0.5,
        iou: 0.45,
        fps_sample: 1
    });

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (selectedFile) => {
        if (!selectedFile.type.startsWith('video/')) {
            setError('Please upload a valid video file');
            return;
        }
        setError(null);
        setFile(selectedFile);
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('confidence_threshold', config.confidence);
        formData.append('iou_threshold', config.iou);
        formData.append('fps_sample', config.fps_sample);

        try {
            const response = await uploadVideo(formData);
            navigate(`/results/${response.video_id}`);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Upload failed');
            setUploading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={`${styles.uploadCard} glass-panel`}>
                <h2 className={styles.title}>Upload Video</h2>
                <p className={styles.subtitle}>Detect brands and logos</p>

                <div
                    className={`${styles.dropZone} ${dragActive ? styles.dragActive : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        className={styles.hiddenInput}
                        onChange={handleChange}
                        accept="video/*"
                    />

                    {file ? (
                        <div className={styles.fileInfo}>
                            <FileVideo size={48} className={styles.iconAccent} />
                            <div className={styles.fileName}>{file.name}</div>
                            <button
                                className={styles.changeBtn}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setFile(null);
                                }}
                            >
                                Change File
                            </button>
                        </div>
                    ) : (
                        <>
                            <UploadCloud size={64} className={styles.icon} />
                            <p className={styles.dropText}>Drag video here</p>
                        </>
                    )}
                </div>

                {error && (
                    <div className={styles.error}>
                        <AlertCircle size={20} />
                        <span>{error}</span>
                    </div>
                )}

                <button
                    className={`${styles.uploadBtn} btn btn-primary`}
                    disabled={!file || uploading}
                    onClick={handleUpload}
                >
                    {uploading ? (
                        <>
                            <Loader2 className={styles.spin} size={20} />
                            <span>Processing...</span>
                        </>
                    ) : (
                        <>
                            <Video size={20} />
                            <span>Analyze</span>
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default VideoUploader;
