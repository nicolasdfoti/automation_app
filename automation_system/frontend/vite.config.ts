import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The browser (Windows) talks to the Automation System API directly at
// 127.0.0.1:8001; the backend already allows localhost:5174 / 127.0.0.1:5174
// via CORS, so no server-side proxy is needed and WSL <-> Windows networking
// is avoided.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5174,
    strictPort: true,
  },
});