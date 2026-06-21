// Frontend environment config for Vercel
// Set environment variable VITE_API_URL on Vercel to your backend API URL
// Example: https://compiler-backend.render.onrender.com

let apiUrl = 'http://localhost:8000';
try {
    const env = new Function('return import.meta.env')();
    if (env && env.VITE_API_URL) {
        apiUrl = env.VITE_API_URL;
    }
} catch (err) {
    // import.meta.env is not available in plain <script> mode,
    // so fall back to localhost for local static hosting.
}

window.API_BASE_URL = apiUrl;
