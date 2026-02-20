import React, { useState } from 'react';
import './ImageUploader.css';

const ImageUploader = ({ onUpload, onClose, loading = false }) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [error, setError] = useState('');

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
            setError('Please select a JPG or PNG image');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            setError('Image size must be less than 5MB');
            return;
        }

        setError('');
        setSelectedFile(file);

        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreview(reader.result);
        };
        reader.readAsDataURL(file);
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        try {
            await onUpload(selectedFile);
            setSelectedFile(null);
            setPreview(null);
        } catch (err) {
            setError(err.message || 'Upload failed');
        }
    };

    return (
        <div className="image-uploader-modal">
            <div className="image-uploader-content">
                <div className="uploader-header">
                    <h3>Upload Ulcer Image</h3>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="uploader-body">
                    <div className="upload-instructions">
                        <p><strong>For best results:</strong></p>
                        <ul>
                            <li>Good lighting</li>
                            <li>Clear foot visibility</li>
                            <li>Clean background</li>
                            <li>JPEG or PNG format</li>
                        </ul>
                    </div>

                    <div className="file-input-wrapper">
                        <input
                            type="file"
                            id="image-upload"
                            accept=".jpg,.jpeg,.png"
                            onChange={handleFileSelect}
                            disabled={loading}
                        />
                        <label htmlFor="image-upload" className="btn btn-secondary">
                            Choose Image
                        </label>
                    </div>

                    {preview && (
                        <div className="image-preview">
                            <img src={preview} alt="Preview" />
                        </div>
                    )}

                    {error && <div className="form-error">{error}</div>}
                </div>

                <div className="uploader-footer">
                    <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
                        Cancel
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleUpload}
                        disabled={!selectedFile || loading}
                    >
                        {loading ? (
                            <>
                                <span className="spinner spinner-sm"></span>
                                Uploading...
                            </>
                        ) : (
                            'Upload & Analyze'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ImageUploader;
