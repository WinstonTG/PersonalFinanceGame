import { defineConfig } from "playwright/test";

export default defineConfig({
  testMatch: "web/ui.e2e.spec.js",
  webServer: {
    command: "python -m http.server 8000 --bind 127.0.0.1 --directory web",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: false,
  },
});
