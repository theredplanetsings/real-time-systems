# Deployment Checklist

Use this checklist when deploying to Streamlit Cloud.

## Pre-deploy

1. Confirm dependencies are pinned in `requirements.txt`.
2. Confirm system packages are declared in `packages.txt`.
3. For PNG exports, ensure `packages.txt` includes `chromium`.
4. Run local checks:

```bash
PYTHONPATH=. pytest -q
```

## Deploy

1. Push the target branch to GitHub.
2. Trigger Streamlit Cloud redeploy.
3. Wait for build and startup to complete.

## Post-deploy smoke checks

1. Open `pages/11_Priority_Inversion.py` and run a schedule.
2. Open `pages/02_Compare_Mode.py`, click `Run Compare`, and expand at least one schedule.
3. Verify `Download schedule PNG` is available and completes.
4. Verify there are no runtime exceptions in the app logs.

## If PNG export fails

1. Check logs for Chrome/Chromium errors.
2. Verify `packages.txt` still contains `chromium`.
3. Redeploy after confirming package and dependency changes.
