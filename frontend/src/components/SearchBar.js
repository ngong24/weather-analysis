import React, { useState, useEffect, useRef } from 'react';
import api from '../utils/api';

const HISTORY_KEY = 'search_history_v1';

// --- Utility Functions ---
const normalizeStr = (str) => {
    if (!str) return '';
    return str.normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
              .replace(/đ/g, "d").replace(/Đ/g, "D")
              .toLowerCase()
              .trim();
};

const isSameLocation = (loc1, loc2) => {
    if (!loc1.latitude || !loc1.longitude || !loc2.latitude || !loc2.longitude) return false;
    return Math.abs(loc1.latitude - loc2.latitude) < 0.01 && 
           Math.abs(loc1.longitude - loc2.longitude) < 0.01;
};

const makeKey = (item) => `${item.name}|${item.country}|${item.admin1}`;

const loadHistory = () => {
    try {
        const raw = localStorage.getItem(HISTORY_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch { return {}; }
};

const saveHistory = (hist) => {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(hist)); } catch {}
};

const highlightMatch = (text, q) => {
    if (!q || !text) return text;
    const escapeRegExp = (string) => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = text.split(new RegExp(`(${escapeRegExp(q)})`, 'gi'));
    return (
        <>
            {parts.map((part, i) => 
                part.toLowerCase() === q.toLowerCase() ? (
                    <strong key={i} style={{ background: 'rgba(255,220,100,0.25)', padding: '0 2px' }}>{part}</strong>
                ) : part
            )}
        </>
    );
};

const SearchBar = ({ onSelectLocation, user }) => {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [activeIndex, setActiveIndex] = useState(-1);
    const [showList, setShowList] = useState(false);
    const [favorites, setFavorites] = useState([]);
    const [isLoading, setIsLoading] = useState(false); // Thêm state loading để UI mượt hơn

    // REFS CHO TỐI ƯU HÓA
    const timerRef = useRef(null);
    const wrapperRef = useRef(null);
    const abortControllerRef = useRef(null); // (A) Để hủy request cũ
    const cacheRef = useRef({});             // (B) Để lưu cache: { "hanoi": [data...] }

    // Load Favorites
    useEffect(() => {
        if (user) {
            const fetchFavorites = async () => {
                try {
                    const res = await api.get('favorites/');
                    setFavorites(Array.isArray(res.data) ? res.data : []);
                } catch (err) { setFavorites([]); }
            };
            fetchFavorites();
        } else { setFavorites([]); }
    }, [user]);

    // Click outside
    useEffect(() => {
        const handler = (e) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setShowList(false);
                setActiveIndex(-1);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const processResults = (q, apiData) => {
        const normalizedQuery = normalizeStr(q);
        const history = loadHistory();

        // 1. Filter Favorites
        const matchedFavorites = favorites.filter(fav => {
            const normName = normalizeStr(fav.city_name);
            return normName.includes(normalizedQuery);
        }).map(fav => ({
            ...fav,
            name: fav.city_name,
            displayName: fav.city_name,
            key: `fav_${fav.id}`,
            isFavorite: true,
            score: 2000, 
            source: 'favorite'
        }));

        // 2. Process API & Merge
        const processedApiResults = [];
        apiData.forEach(item => {
            // Deduplicate
            const duplicateFav = matchedFavorites.find(fav => isSameLocation(fav, item));
            if (duplicateFav) return; 

            const key = makeKey(item);
            const count = history[key]?.count || 0;
            
            const normName = normalizeStr(item.name);
            let score = count * 100;
            if (normName.startsWith(normalizedQuery)) score += 50;
            else if (normName.includes(normalizedQuery)) score += 20;

            const displayName = `${item.name}${item.admin1 ? ', ' + item.admin1 : ''}${item.country ? ', ' + item.country : ''}`;

            processedApiResults.push({
                ...item,
                key,
                count,
                score,
                displayName,
                isFavorite: false,
                source: 'api'
            });
        });

        const finalResults = [...matchedFavorites, ...processedApiResults];
        finalResults.sort((a, b) => b.score - a.score);
        return finalResults;
    };

    const fetchSuggestions = async (q) => {
        if (!q || q.trim() === '') {
            setSuggestions([]);
            return;
        }

        const normalizedKey = normalizeStr(q); // Dùng key đã chuẩn hóa cho cache

        // (B) CACHE CHECK: Nếu đã có trong cache thì trả về luôn, KHÔNG gọi API
        if (cacheRef.current[normalizedKey]) {
            setSuggestions(cacheRef.current[normalizedKey]);
            setShowList(true);
            return; 
        }

        // (A) ABORT OLD REQUEST: Hủy request trước đó nếu nó đang chạy
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        // Tạo controller mới cho request hiện tại
        abortControllerRef.current = new AbortController();

        setIsLoading(true);

        try {
            const res = await api.get(`search-city/?city=${encodeURIComponent(q)}`, {
                signal: abortControllerRef.current.signal // Gắn signal vào axios
            });
            
            const list = Array.isArray(res.data) ? res.data : [];
            const finalResults = processResults(q, list);

            // Lưu vào cache
            cacheRef.current[normalizedKey] = finalResults;

            setSuggestions(finalResults);
            setShowList(true);
            setActiveIndex(-1);
            setIsLoading(false);

        } catch (err) {
            // Nếu lỗi do mình tự hủy (Abort) thì không làm gì cả (để tránh set state trên unmounted component)
            if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
                return; 
            }
            console.error(err);
            setSuggestions([]); // Có thể giữ suggestions cũ nếu muốn, hoặc clear
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => {
            fetchSuggestions(query);
        }, 180);
        return () => { if (timerRef.current) clearTimeout(timerRef.current); };
    }, [query]);

    const commitSelection = (item) => {
        if (!item) return;
        const payload = { latitude: item.latitude, longitude: item.longitude, name: item.name, country: item.country };
        
        const hist = loadHistory();
        const key = item.source === 'api' ? makeKey(item) : `fav_${item.id}`;
        
        hist[key] = hist[key] || { count: 0, item };
        hist[key].count += 1;
        saveHistory(hist);

        setQuery(item.name);
        setShowList(false);
        setActiveIndex(-1);
        if (onSelectLocation) onSelectLocation(payload);
    };

    const handleKeyDown = (e) => {
        if (!showList) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActiveIndex((i) => Math.max(i - 1, 0));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0 && activeIndex < suggestions.length) commitSelection(suggestions[activeIndex]);
            else if (query.trim() !== '' && suggestions.length > 0) commitSelection(suggestions[0]);
        } else if (e.key === 'Escape') {
            setShowList(false);
            setActiveIndex(-1);
        }
    };

    return (
        <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(255,255,255,0.9)', padding: '8px 14px', borderRadius: 30 }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 21l-4.35-4.35" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/><circle cx="11" cy="11" r="6" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                <input
                    placeholder="Search city..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => { if (suggestions.length) setShowList(true); }}
                    style={{ border: 'none', outline: 'none', background: 'transparent', marginLeft: 10, width: '100%', fontSize: 15 }}
                />
                 {/* Chỉ báo loading nhỏ góc phải input (Optional) */}
                {isLoading && <div style={{width: 14, height: 14, border: '2px solid #ddd', borderTopColor: '#666', borderRadius: '50%', animation: 'spin 0.6s linear infinite'}}></div>}
                <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
            </div>

            {showList && suggestions.length > 0 && (
                <div style={{ position: 'absolute', left: 0, right: 0, marginTop: 8, background: 'white', borderRadius: 10, boxShadow: '0 6px 20px rgba(0,0,0,0.08)', zIndex: 60, maxHeight: 300, overflow: 'auto' }}>
                    {suggestions.map((s, idx) => (
                        <div
                            key={s.key || idx}
                            onMouseEnter={() => setActiveIndex(idx)}
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={() => commitSelection(s)}
                            style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', cursor: 'pointer', background: idx === activeIndex ? '#f0f9ff' : 'transparent', borderBottom: '1px solid rgba(0,0,0,0.03)' }}
                        >
                            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                <div style={{ width: 6, height: 6, borderRadius: 6, background: '#2b8aef' }} />
                                <div style={{ fontSize: 14, color: '#222' }}>{highlightMatch(s.displayName, query)}</div>
                            </div>
                            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                {s.isFavorite && <span style={{ background: '#ffe6d6', color: '#d97706', fontSize: 12, padding: '3px 6px', borderRadius: 12 }}>⭐ Favorite</span>}
                                {s.count > 0 && !s.isFavorite && <span style={{ background: '#e8f8ff', color: '#0466b3', fontSize: 12, padding: '3px 6px', borderRadius: 12 }}>Recent</span>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SearchBar;