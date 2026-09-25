# Homebase frontend

The Coffee module has a recent-recipes page at `/coffee` and a New Recipe form at `/coffee/new`. The form saves to the FastAPI coffee API and uses its suggestions endpoint for free-text lookup fields.

The shared Material UI light theme lives in `src/theme.ts`. It uses forest green for primary actions, clay for secondary accents, a warm paper background, sage highlights, Newsreader headings, and DM Sans body text.

From `frontend/`, run `npm install`, then `npm run dev`. Vite proxies `/api` to the backend at `http://localhost:8000`.

Verify changes with:

```sh
npm test
npm run lint
npm run build
```
