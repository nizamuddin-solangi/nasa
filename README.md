# EARTHSCOPE

NASA Space Apps Challenge 2026 MVP for investigating Earth-system trends with genuine NASA POWER monthly point data.

## Run

```powershell
python -m uvicorn app.main:app --app-dir backend --reload
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). The API runs at `http://localhost:8000`.

## Verification

```powershell
$env:PYTHONPATH='backend'; python -m pytest backend/tests -q
npm run build
```

The frontend never contains observation arrays: it requests NASA POWER through FastAPI. If NASA POWER is unavailable, the UI reports that condition and does not substitute data. NASA POWER monthly meteorological values use GMAO MERRA-2; radiation provenance is CERES/GEWEX SRB, as surfaced alongside every investigation.

## Production deployment

The backend includes a [Render blueprint](render.yaml) with a persistent disk for SQLite and `EARTHSCOPE_CORS_ORIGINS` for the deployed Vercel origin. Deploy the frontend with Vercel using `VITE_API_URL=https://<your-api-host>`. The Dockerfile can be used on any container-compatible FastAPI host. FastAPI's interactive API documentation is available at `/docs`.

This repository does not contain hosting credentials or a connected Git remote, so deployment must be authorized from the owner's Vercel/Render accounts before public URLs can be created.
