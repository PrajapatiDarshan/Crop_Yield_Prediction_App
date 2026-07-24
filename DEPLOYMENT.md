# Deploying the Live Demo

I can't register a live URL or push to GitHub on your behalf — Streamlit Community Cloud
requires your own GitHub account and a login-authenticated deploy step. Here's how to get
`https://<your-app-name>.streamlit.app` live in about 2 minutes:

## 1. Push this project to GitHub
```bash
cd crop_yield_project
git init
git add .
git commit -m "Crop yield prediction capstone"
git branch -M main
git remote add origin https://github.com/<your-username>/crop-yield-prediction.git
git push -u origin main
```
(Create the empty repo on GitHub first, named e.g. `crop-yield-prediction`.)

> Note: `models/best_model.pkl` and the CSVs under `data/` are already git-safe (no secrets,
> no proprietary data). If your repo has a file-size limit concern, `models/all_models.pkl`
> (~19MB) is optional — the dashboard only needs `best_model.pkl` (~550KB).

## 2. Deploy on Streamlit Community Cloud
1. Go to **share.streamlit.io** and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repo, branch `main`, and set the main file path to:
   ```
   dashboard/app.py
   ```
4. Click **Deploy**. Streamlit Cloud will install `requirements.txt` automatically and give
   you a URL like:
   ```
   https://crop-yield-prediction.streamlit.app
   ```
5. Update the README's "Live Demo" link with your actual URL once it's issued.

## 3. Keep it updated
Any `git push` to `main` automatically redeploys the app — no extra steps needed.

## Troubleshooting
- **App boots but shows an error about missing files**: make sure `data/processed/`,
  `models/`, and `reports/` were committed (check `.gitignore` doesn't exclude them —
  it currently only excludes caches and virtual envs, not data).
- **Slow first load**: the first request after idling spins the app back up (free tier
  sleeps after inactivity) — this is normal for Streamlit Community Cloud's free tier.
