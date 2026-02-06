import React from 'react';

const HistoryTable = ({ history, onDelete, onClearAll }) => {
    const formatDate = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleString('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatUrl = (url) => {
        if (url.length > 50) {
            return url.substring(0, 47) + '...';
        }
        return url;
    };

    if (!history || history.length === 0) {
        return (
            <div className="empty-history">
                <div className="empty-icon">📭</div>
                <h3>No hay análisis previos</h3>
                <p>Los análisis que realices aparecerán aquí</p>
            </div>
        );
    }

    return (
        <div className="history-container">
            <div className="history-header">
                <h2>📊 Historial de Análisis</h2>
                <button className="btn-clear-all" onClick={onClearAll}>
                    🗑️ Limpiar Todo
                </button>
            </div>

            <div className="table-wrapper">
                <table className="history-table">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>URL del Video</th>
                            <th>Logos Detectados</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history.map((item, index) => (
                            <tr key={index}>
                                <td className="date-cell">{formatDate(item.timestamp)}</td>
                                <td className="url-cell">
                                    <a href={item.url} target="_blank" rel="noopener noreferrer" title={item.url}>
                                        {formatUrl(item.url)}
                                    </a>
                                </td>
                                <td className="logos-cell">
                                    <span className="logo-count">{item.logoCount}</span>
                                    {item.logos && item.logos.length > 0 && (
                                        <div className="logo-names">
                                            {item.logos.slice(0, 3).map((logo, i) => (
                                                <span key={i} className="logo-badge">{logo.name}</span>
                                            ))}
                                            {item.logos.length > 3 && (
                                                <span className="logo-badge more">+{item.logos.length - 3}</span>
                                            )}
                                        </div>
                                    )}
                                </td>
                                <td className="actions-cell">
                                    <button
                                        className="btn-delete"
                                        onClick={() => onDelete(index)}
                                        title="Eliminar"
                                    >
                                        🗑️
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default HistoryTable;
