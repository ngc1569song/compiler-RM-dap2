window.CONFIG = {
  API_BASE_URL:
    window.location.hostname === "localhost"
      ? "http://localhost:8000"
      : "https://compiler-dap2-production.up.railway.app"
};