import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getNearbyDoctors } from '../api/placesApi';
import './NearbyDoctorsPage.css';

const DOCTOR_TYPES = [
    { id: 'podiatrist', label: 'Podiatrist' },
    { id: 'physician', label: 'Physician' },
    { id: 'diabetologist', label: 'Diabetologist' }
];

const SORT_OPTIONS = [
    { id: 'relevance', label: 'Relevance' },
    { id: 'distance', label: 'Distance' }
];

const RATING_OPTIONS = [
    { id: 'any', label: 'Any', value: 0 },
    { id: '3.5', label: '3.5', value: 3.5, star: true },
    { id: '4.0', label: '4.0', value: 4.0, star: true },
    { id: '4.5', label: '4.5', value: 4.5, star: true }
];

const REVIEW_OPTIONS = [
    { id: 'any', label: 'Any', value: 0 },
    { id: '30+', label: '30+', value: 30 },
    { id: '90+', label: '90+', value: 90 },
    { id: '300+', label: '300+', value: 300 }
];

const AVAILABILITY_OPTIONS = [
    { id: 'any', label: 'Any' },
    { id: 'open', label: 'Open' },
    { id: 'closed', label: 'Closed' }
];

// Helper to format opening status like Google Maps
const formatOpenStatus = (doctor) => {
    if (doctor.open_now === null || doctor.open_now === undefined) {
        return { status: 'Hours not available', timeInfo: null, isOpen: null };
    }

    const now = new Date();
    const currentDay = now.getDay(); // 0 = Sunday
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTimeMinutes = currentHour * 60 + currentMinute;

    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    // Parse time string like "9:00 AM" or "9:00 am" to minutes since midnight  
    const parseTime = (timeStr) => {
        if (!timeStr) return null;
        const match = timeStr.trim().match(/(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?/i);
        if (!match) return null;
        let hours = parseInt(match[1]);
        const minutes = parseInt(match[2]);
        const period = match[3]?.toUpperCase();

        if (period === 'PM' && hours !== 12) hours += 12;
        if (period === 'AM' && hours === 12) hours = 0;

        return hours * 60 + minutes;
    };

    // Format minutes to readable time
    const formatTime = (minutes) => {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        const period = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        return mins === 0 ? `${displayHours} ${period}` : `${displayHours}:${mins.toString().padStart(2, '0')} ${period}`;
    };

    // Get hours for a specific day
    const getHoursForDay = (dayIndex) => {
        const dayName = dayNames[dayIndex];
        return doctor.opening_hours?.find(h => h.startsWith(dayName));
    };

    // Parse open and close times from hours string (e.g., "Monday: 9:00 AM – 8:00 PM")
    const parseHoursString = (hoursStr) => {
        if (!hoursStr || hoursStr.toLowerCase().includes('closed')) return null;
        const timeMatch = hoursStr.match(/:\s*(.+?)\s*[–-]\s*(.+?)$/);
        if (!timeMatch) return null;
        return {
            open: parseTime(timeMatch[1]),
            close: parseTime(timeMatch[2])
        };
    };

    const todayHours = getHoursForDay(currentDay);
    const todayTimes = parseHoursString(todayHours);

    if (doctor.open_now) {
        // Currently OPEN - find when it closes
        if (todayTimes && todayTimes.close !== null) {
            return { status: 'Open', timeInfo: `Closes ${formatTime(todayTimes.close)}`, isOpen: true };
        }
        return { status: 'Open', timeInfo: null, isOpen: true };
    } else {
        // Currently CLOSED - find when it opens next

        // Check if it opens later TODAY
        if (todayTimes && todayTimes.open !== null && todayTimes.open > currentTimeMinutes) {
            return { status: 'Closed', timeInfo: `Opens ${formatTime(todayTimes.open)}`, isOpen: false };
        }

        // Check upcoming days (tomorrow through next week)
        for (let i = 1; i <= 7; i++) {
            const nextDayIndex = (currentDay + i) % 7;
            const nextDayHours = getHoursForDay(nextDayIndex);
            const nextDayTimes = parseHoursString(nextDayHours);

            if (nextDayTimes && nextDayTimes.open !== null) {
                const timeStr = formatTime(nextDayTimes.open);
                if (i === 1) {
                    return { status: 'Closed', timeInfo: `Opens ${timeStr} tomorrow`, isOpen: false };
                } else {
                    const dayAbbrev = dayNames[nextDayIndex].slice(0, 3);
                    return { status: 'Closed', timeInfo: `Opens ${dayAbbrev} ${timeStr}`, isOpen: false };
                }
            }
        }

        return { status: 'Closed', timeInfo: null, isOpen: false };
    }
};

const NearbyDoctorsPage = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [location, setLocation] = useState(null);
    const [doctors, setDoctors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Filters
    const [selectedTypes, setSelectedTypes] = useState([]);
    const [sortBy, setSortBy] = useState('distance');
    const [minRating, setMinRating] = useState('any');
    const [minReviews, setMinReviews] = useState('any');
    const [availability, setAvailability] = useState('any');
    const [showFilters, setShowFilters] = useState(false);

    // Initialize selected types from URL params
    useEffect(() => {
        const doctorTypesParam = searchParams.get('doctorTypes');
        if (doctorTypesParam) {
            const types = doctorTypesParam.split(',').filter(t =>
                DOCTOR_TYPES.some(dt => dt.id === t)
            );
            if (types.length > 0) {
                setSelectedTypes(types);
            }
        }
    }, [searchParams]);

    // Get user location on mount
    useEffect(() => {
        if (!navigator.geolocation) {
            setError('Geolocation is not supported by your browser');
            setLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setLocation({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
            },
            (err) => {
                setError('Unable to get your location. Please enable location access.');
                setLoading(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }, []);

    // Fetch doctors when location or type filters change
    const fetchDoctors = useCallback(async () => {
        if (!location) return;

        setLoading(true);
        setError(null);

        try {
            const data = await getNearbyDoctors(
                location.latitude,
                location.longitude,
                10000,
                selectedTypes
            );
            setDoctors(data.places || []);
        } catch (err) {
            setError('Failed to fetch nearby doctors. Please try again.');
            console.error('Error fetching doctors:', err);
        } finally {
            setLoading(false);
        }
    }, [location, selectedTypes]);

    useEffect(() => {
        if (location) {
            fetchDoctors();
        }
    }, [location, selectedTypes, fetchDoctors]);

    // Toggle doctor type filter
    const toggleType = (typeId) => {
        setSelectedTypes(prev =>
            prev.includes(typeId)
                ? prev.filter(t => t !== typeId)
                : [...prev, typeId]
        );
    };

    // Apply filters and sorting
    const filteredDoctors = useMemo(() => {
        let filtered = [...doctors];

        // Filter by rating
        const ratingOption = RATING_OPTIONS.find(r => r.id === minRating);
        if (ratingOption && ratingOption.value > 0) {
            filtered = filtered.filter(d => (d.rating || 0) >= ratingOption.value);
        }

        // Filter by reviews
        const reviewOption = REVIEW_OPTIONS.find(r => r.id === minReviews);
        if (reviewOption && reviewOption.value > 0) {
            filtered = filtered.filter(d => (d.user_ratings_total || 0) >= reviewOption.value);
        }

        // Filter by availability
        if (availability === 'open') {
            filtered = filtered.filter(d => d.open_now === true);
        } else if (availability === 'closed') {
            filtered = filtered.filter(d => d.open_now === false);
        }

        // Sort
        if (sortBy === 'distance') {
            filtered.sort((a, b) => (a.distance_meters || Infinity) - (b.distance_meters || Infinity));
        } else {
            // Relevance - sort by rating then distance
            filtered.sort((a, b) => {
                const ratingDiff = (b.rating || 0) - (a.rating || 0);
                if (Math.abs(ratingDiff) > 0.5) return ratingDiff;
                return (a.distance_meters || Infinity) - (b.distance_meters || Infinity);
            });
        }

        return filtered;
    }, [doctors, minRating, minReviews, availability, sortBy]);

    const activeFilterCount = useMemo(() => {
        let count = 0;
        if (minRating !== 'any') count++;
        if (minReviews !== 'any') count++;
        if (availability !== 'any') count++;
        return count;
    }, [minRating, minReviews, availability]);

    return (
        <div className="nearby-doctors-page">
            <div className="nearby-doctors-container">
                {/* Header with Back Button */}
                <header className="page-header">
                    <button className="back-btn" onClick={() => navigate('/')}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M15 18l-6-6 6-6" />
                        </svg>
                        <span>Home</span>
                    </button>
                    <h1>Find Nearby Doctors</h1>
                    <p className="header-subtitle">Locate specialists near you within 10km</p>
                </header>

                {/* Doctor Type Chips */}
                <div className="filter-section type-filters">
                    <div className="filter-chips">
                        {DOCTOR_TYPES.map(type => (
                            <button
                                key={type.id}
                                className={`filter-chip ${selectedTypes.includes(type.id) ? 'active' : ''}`}
                                onClick={() => toggleType(type.id)}
                            >
                                {selectedTypes.includes(type.id) && (
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                        <polyline points="20 6 9 17 4 12" />
                                    </svg>
                                )}
                                {type.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Filter Bar */}
                <div className="filter-bar">
                    {/* Sort Toggle */}
                    <div className="sort-toggle">
                        {SORT_OPTIONS.map(opt => (
                            <button
                                key={opt.id}
                                className={`sort-btn ${sortBy === opt.id ? 'active' : ''}`}
                                onClick={() => setSortBy(opt.id)}
                            >
                                {sortBy === opt.id && (
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                        <polyline points="20 6 9 17 4 12" />
                                    </svg>
                                )}
                                {opt.label}
                            </button>
                        ))}
                    </div>

                    {/* Filters Button */}
                    <button
                        className={`filters-btn ${activeFilterCount > 0 ? 'has-filters' : ''}`}
                        onClick={() => setShowFilters(!showFilters)}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="4" y1="6" x2="20" y2="6" />
                            <line x1="4" y1="12" x2="20" y2="12" />
                            <line x1="4" y1="18" x2="20" y2="18" />
                            <circle cx="8" cy="6" r="2" fill="currentColor" />
                            <circle cx="16" cy="12" r="2" fill="currentColor" />
                            <circle cx="10" cy="18" r="2" fill="currentColor" />
                        </svg>
                        Filters
                        {activeFilterCount > 0 && <span className="filter-count">{activeFilterCount}</span>}
                    </button>
                </div>

                {/* Expandable Filters Panel */}
                {showFilters && (
                    <div className="filters-panel slide-up">
                        <div className="filter-group">
                            <span className="filter-label">Rating</span>
                            <div className="filter-options">
                                {RATING_OPTIONS.map(opt => (
                                    <button
                                        key={opt.id}
                                        className={`option-btn ${minRating === opt.id ? 'active' : ''}`}
                                        onClick={() => setMinRating(opt.id)}
                                    >
                                        {minRating === opt.id && (
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        )}
                                        {opt.label}
                                        {opt.star && <span className="star">★</span>}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="filter-group">
                            <span className="filter-label">Number of reviews</span>
                            <div className="filter-options">
                                {REVIEW_OPTIONS.map(opt => (
                                    <button
                                        key={opt.id}
                                        className={`option-btn ${minReviews === opt.id ? 'active' : ''}`}
                                        onClick={() => setMinReviews(opt.id)}
                                    >
                                        {minReviews === opt.id && (
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        )}
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="filter-group">
                            <span className="filter-label">Availability</span>
                            <div className="filter-options">
                                {AVAILABILITY_OPTIONS.map(opt => (
                                    <button
                                        key={opt.id}
                                        className={`option-btn ${availability === opt.id ? 'active' : ''}`}
                                        onClick={() => setAvailability(opt.id)}
                                    >
                                        {availability === opt.id && (
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        )}
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Results Count */}
                {!loading && !error && (
                    <div className="results-info">
                        <span>{filteredDoctors.length} results found</span>
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="loading-container">
                        <div className="spinner"></div>
                        <p>Finding doctors near you...</p>
                    </div>
                )}

                {/* Error State */}
                {error && !loading && (
                    <div className="error-container">
                        <svg className="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        <h3>Location Error</h3>
                        <p>{error}</p>
                        <button className="btn btn-primary" onClick={() => window.location.reload()}>
                            Try Again
                        </button>
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && filteredDoctors.length === 0 && (
                    <div className="empty-state">
                        <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                            <circle cx="9" cy="7" r="4" />
                            <line x1="23" y1="11" x2="17" y2="11" />
                        </svg>
                        <h3>No Doctors Found</h3>
                        <p>Try adjusting your filters or expanding your search.</p>
                    </div>
                )}

                {/* Doctor Cards */}
                {!loading && !error && filteredDoctors.length > 0 && (
                    <div className="doctors-grid">
                        {filteredDoctors.map(doctor => {
                            const openStatus = formatOpenStatus(doctor);

                            return (
                                <div key={doctor.place_id} className="doctor-card">
                                    <div className="card-main">
                                        <div className="card-header">
                                            <h3 className="doctor-name">{doctor.name}</h3>
                                            <span className="distance-badge">{doctor.distance_text}</span>
                                        </div>

                                        {/* Rating */}
                                        {doctor.rating && (
                                            <div className="rating-row">
                                                <span className="rating-value">{doctor.rating.toFixed(1)}</span>
                                                <div className="stars">
                                                    {[1, 2, 3, 4, 5].map(i => (
                                                        <svg key={i} viewBox="0 0 24 24" className={i <= Math.round(doctor.rating) ? 'filled' : ''}>
                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                        </svg>
                                                    ))}
                                                </div>
                                                <span className="review-count">({doctor.user_ratings_total})</span>
                                            </div>
                                        )}

                                        {/* Address */}
                                        <p className="address">{doctor.address}</p>

                                        {/* Open Status */}
                                        <div className="open-status">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <circle cx="12" cy="12" r="10" />
                                                <polyline points="12 6 12 12 16 14" />
                                            </svg>
                                            <span className={openStatus.isOpen === true ? 'status-open' : openStatus.isOpen === false ? 'status-closed' : 'status-unknown'}>
                                                {openStatus.status}
                                            </span>
                                            {openStatus.timeInfo && (
                                                <span className="time-info">· {openStatus.timeInfo}</span>
                                            )}
                                        </div>

                                        {/* Contact Info */}
                                        <div className="contact-section">
                                            {doctor.phone && (
                                                <div className="contact-row">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                                                    </svg>
                                                    <span>{doctor.phone}</span>
                                                    <a href={`tel:${doctor.phone}`} className="icon-btn call-btn" title="Call">
                                                        <svg viewBox="0 0 24 24" fill="currentColor">
                                                            <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 0 0-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z" />
                                                        </svg>
                                                    </a>
                                                </div>
                                            )}

                                            {doctor.website && (
                                                <div className="contact-row">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <circle cx="12" cy="12" r="10" />
                                                        <line x1="2" y1="12" x2="22" y2="12" />
                                                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                                    </svg>
                                                    <span className="website-url">{doctor.website.replace(/^https?:\/\//, '').split('/')[0]}</span>
                                                    <a href={doctor.website} target="_blank" rel="noopener noreferrer" className="icon-btn web-btn" title="Open website">
                                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                                            <polyline points="15 3 21 3 21 9" />
                                                            <line x1="10" y1="14" x2="21" y2="3" />
                                                        </svg>
                                                    </a>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Action Button */}
                                    <a
                                        href={doctor.google_maps_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="maps-btn"
                                    >
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polygon points="3 11 22 2 13 21 11 13 3 11" />
                                        </svg>
                                        Directions
                                    </a>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default NearbyDoctorsPage;
