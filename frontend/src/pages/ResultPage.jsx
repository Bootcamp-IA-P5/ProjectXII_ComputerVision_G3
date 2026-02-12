import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import Layout from '../components/Layout';
import ResultsDashboard from '../components/ResultsDashboard';
import { getVideos, getVideoResult } from '../services/api'; // getVideos gets list, need getVideo(id)
import axios from 'axios';
import { Loader2, ArrowLeft, AlertTriangle } from 'lucide-react';
import styles from './ResultPage.module.css';

// We need a specific getVideo function in api.js, but we can reuse axios here or just use /videos endpoint
// Actually, earlier I defined getVideoResult but not getVideo metadata fetcher specifically in api.js?
// I defined `getVideos` (list).
// I should use axios directly for now to fetch /videos/{id} or add it to api.js.
// I'll add it to this file for simplicity or just use axios.

const ResultPage = () => {
    const { id } = useParams();
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(true);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [videoMeta, setVideoMeta] = useState(null);

    const pollInterval = useRef(null);

    useEffect(() => {
        checkStatus();

        // Poll every 3 seconds
        pollInterval.current = setInterval(checkStatus, 3000);

        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current);
        };
    }, [id]);

    const checkStatus = async () => {
        try {
            // 1. Get Video Metadata to check processing status
            const { data: video } = await axios.get(`http://localhost:8000/videos/${id}`);
            setVideoMeta(video);

            if (video.processed_at) {
                // Stop polling and fetch detailed results
                clearInterval(pollInterval.current);
                fetchResults();
                setProcessing(false);
            } else {
                // Still processing
                setProcessing(true);
                setLoading(false);
            }
        } catch (err) {
            console.error(err);
            setError('Video not found or API error');
            setLoading(false);
            clearInterval(pollInterval.current);
        }
    };

    const fetchResults = async () => {
        try {
            setLoading(true);
            const data = await getVideoResult(id);
            setResults(data);
        } catch (err) {
            setError('Failed to load results');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout>
            <div className={styles.container}>
                <div className={styles.actions}>
                    <Link to="/" className="btn btn-secondary">
                        <ArrowLeft size={16} /> Back to Upload
                    </Link>
                </div>

                {error ? (
                    <div className={styles.errorState}>
                        <AlertTriangle size={48} />
                        <h2>Error</h2>
                        <p>{error}</p>
                    </div>
                ) : processing ? (
                    <div className={`${styles.processingState} glass-panel`}>
                        <Loader2 size={48} className="spin" />
                        <h2>Processing Video...</h2>
                        <p>Our AI is detecting brands frame by frame.</p>
                        <p className={styles.meta}>Filename: {videoMeta?.filename}</p>
                        <div className={styles.progressBar}>
                            <div className={styles.progressFill}></div>
                        </div>
                    </div>
                ) : (
                    <ResultsDashboard results={results} />
                )}
            </div>

            <style>{`
        .spin { animation: spin 2s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}</style>
        </Layout>
    );
};

export default ResultPage;
