import { defineConfig } from "playwright/test";

export default defineConfig({
  testMatch: "web/*.e2e.spec.js",
  webServer: [{
    command: "python -m finance_game.server --port 8000 --database test-results/documents.sqlite3",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: false,
  }, {
    command: "npm run build && python -m http.server 8003 --bind 127.0.0.1 --directory dist",
    url: "http://127.0.0.1:8003",
    reuseExistingServer: false,
  }],
});
