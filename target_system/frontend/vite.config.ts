import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The browser (Windows) talks to FastAPI directly at 127.0.0.1:8000; the
// backend already allows localhost:5173 / 127.0.0.1:5173 via CORS, so no
// server-side proxy is needed and WSL <-> Windows networking is avoided.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
  },
});