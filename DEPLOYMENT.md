# InternPath AI - Production Deployment Guide

This guide details deploying InternPath AI to cloud platforms (Render or Railway) connected to Supabase PostgreSQL.

---

## 1. Supabase PostgreSQL Setup
1. Create a free account at [Supabase](https://supabase.com).
2. Create a new project (e.g. `internpath-db`).
3. Open **Project Settings** -> **Database**.
4. Copy the **Connection URI** (Use the Connection Pooler string mode `Session` on port 5432 or 6543):
   `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
5. Open the **SQL Editor** tab in Supabase, paste the contents of `database/schema.postgres.sql`, and click **Run**.

---

## 2. Render Deployment
1. Sign up / Log in to [Render](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository (`InternPath-AI`).
4. Configure service settings:
   * **Name:** `internpath-ai`
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python run.py`
5. Under **Environment Variables**, add:
   * `SECRET_KEY`: (A secure random secret key)
   * `AI_MODE`: `demo` (or `openai` if adding an API key)
   * `DATABASE_URL`: (Paste your Supabase connection string from step 1)
   * `PYTHON_VERSION`: `3.10.12`
6. Click **Deploy Web Service**.

---

## 3. Free Host Keep-Alive Ping
Free tier instances on Render or Railway spin down after 15 minutes of inactivity.
To keep your demo responsive during presentation day:
1. Use a free monitoring service like [UptimeRobot](https://uptimerobot.com) or [Cron-Job.org](https://cron-job.org).
2. Configure a periodic HTTP GET ping every 10–14 minutes to:
   `https://<your-render-app>.onrender.com/api/health`

---

## 4. Pre-Demo Checklist
* [ ] Database tables created on Supabase.
* [ ] Seed users populated (`student@demo.com`, `admin@demo.com`).
* [ ] `/api/health` responds with `{"ok": true, "status": "healthy"}`.
* [ ] HTTPS enabled on deployment URL.
* [ ] Checked that demo credentials work on the live URL.
