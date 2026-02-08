import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { Clock, Eye, Layers, FileVideo } from 'lucide-react';
import styles from './ResultsDashboard.module.css';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

const ResultsDashboard = ({ results }) => {
    if (!results) return null;

    const { video, brands, total_detections, processing_time_seconds } = results;

    // Prepare chart data
    const brandLabels = Object.keys(brands);
    const brandCounts = brandLabels.map(b => brands[b].detections);
    const brandTimes = brandLabels.map(b => brands[b].screen_time_seconds);
    const brandConfidences = brandLabels.map(b => (brands[b].avg_confidence * 100).toFixed(1));

    const barData = {
        labels: brandLabels,
        datasets: [
            {
                label: 'Detections',
                data: brandCounts,
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: '#3b82f6',
                borderWidth: 1,
            },
            {
                label: 'Screen Time (s)',
                data: brandTimes,
                backgroundColor: 'rgba(139, 92, 246, 0.7)',
                borderColor: '#8b5cf6',
                borderWidth: 1,
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8' }
            },
            title: {
                display: true,
                text: 'Brand Presence Analysis',
                color: '#f8fafc'
            }
        },
        scales: {
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                ticks: { color: '#94a3b8' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#94a3b8' }
            }
        }
    };

    return (
        <div className={styles.dashboard}>
            {/* Video Info Card */}
            <div className={`${styles.statsGrid} glass-panel`}>
                <div className={styles.videoPlayer}>
                    {/* 
                For MVP we just verify result logic. 
                In real app we need to serve the video file via a static/stream endpoint.
                Assuming backend serves /static/videos/{filename}
             */}
                    <div className={styles.placeholderVideo}>
                        <FileVideo size={48} />
                        <p>Video Preview Placeholder</p>
                        <small>{video.filename}</small>
                    </div>
                </div>

                <div className={styles.metrics}>
                    <div className={styles.metricCard}>
                        <Layers className={styles.icon} />
                        <div>
                            <h3>{total_detections}</h3>
                            <p>Total Detections</p>
                        </div>
                    </div>

                    <div className={styles.metricCard}>
                        <Eye className={styles.icon} />
                        <div>
                            <h3>{Object.keys(brands).length}</h3>
                            <p>Unique Brands</p>
                        </div>
                    </div>

                    <div className={styles.metricCard}>
                        <Clock className={styles.icon} />
                        <div>
                            <h3>{video.duration_seconds.toFixed(1)}s</h3>
                            <p>Duration</p>
                        </div>
                    </div>

                    <div className={styles.metricCard}>
                        <FileVideo className={styles.icon} />
                        <div>
                            <h3>{video.fps.toFixed(1)}</h3>
                            <p>FPS</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className={`${styles.chartCard} glass-panel`}>
                <Bar options={chartOptions} data={barData} />
            </div>

            {/* Detailed Brand Stats Table */}
            <div className={`${styles.tableCard} glass-panel`}>
                <h3>Brand details</h3>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>Brand</th>
                            <th>Detections</th>
                            <th>Avg Confidence</th>
                            <th>Screen Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.values(brands).map((brand) => (
                            <tr key={brand.brand_name}>
                                <td>{brand.brand_name}</td>
                                <td>{brand.detections}</td>
                                <td>{(brand.avg_confidence * 100).toFixed(1)}%</td>
                                <td>{brand.screen_time_seconds.toFixed(2)}s</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ResultsDashboard;
