import React, { useState } from 'react';
import './SummaryModal.css';

const SummaryModal = ({ summary, onClose }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(summary);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    // Simple markdown-like formatting for summary
    const formatSummary = (text) => {
        if (!text) return '';

        // Convert **bold** to <strong>
        let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Preserve line breaks
        formatted = formatted.replace(/\n/g, '<br />');

        return formatted;
    };

    return (
        <div className="summary-modal">
            <div className="summary-modal-content">
                <div className="summary-header">
                    <h3>Patient Summary</h3>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="summary-body">
                    <div
                        className="summary-text"
                        dangerouslySetInnerHTML={{ __html: formatSummary(summary) }}
                    />
                </div>

                <div className="summary-footer">
                    <button className="btn btn-secondary" onClick={onClose}>
                        Close
                    </button>
                    <button className="btn btn-primary" onClick={handleCopy}>
                        {copied ? (
                            <>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                                Copied!
                            </>
                        ) : (
                            <>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                                </svg>
                                Copy to Clipboard
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SummaryModal;
