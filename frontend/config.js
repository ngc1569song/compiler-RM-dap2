// Frontend API Configuration
// ===========================
// In LOCAL development: points to localhost:8000 (your backend dev server).
// In PRODUCTION (Vercel/Docker): uses same-origin empty string, because
// the platform reverse-proxies /api/* requests to the real backend.
// This means the frontend NEVER needs to know the backend's real URL.

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.API_BASE_URL = 'http://localhost:8000';
} else {
    // In production, /api/* is proxied by Vercel rewrites or nginx reverse proxy.
    // Empty string = same origin = the browser calls its own domain.
    window.API_BASE_URL = '';
}
