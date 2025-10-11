import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Set host to '0.0.0.0' to listen on all local IPs,
    // making it accessible over the network (e.g., from your mobile).
    host: '0.0.0.0', 
    // You can optionally keep or specify the port
    port: 5173,
  },
})