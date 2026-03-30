# Blood Pressure Tracker

A personal blood pressure tracking dashboard built with Streamlit. Supports two users with separate data, medication logging, trend charts, and statistics.

## Features

- **User selection** — choose between Cameron and Jamie on the home screen; all data is stored and displayed per user
- **Log readings** — record systolic, diastolic, pulse, arm, position, and notes; date/time defaults to now but is editable
- **Medication log** — log medication name, dosage, and time taken
- **History** — filterable table of all past readings with a date range picker; delete individual readings
- **Charts** — line charts for systolic/diastolic and pulse over selectable time periods (7/30/90 days or all)
- **Statistics** — averages, highs/lows, total readings, and a 7-day vs previous 7-day comparison

## Running Locally

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the app:**
```bash
streamlit run app.py
```

Data is stored in a local SQLite database (`blood_pressure.db`) in the project folder.

## Deploying to Streamlit Community Cloud

The local SQLite database is not suitable for cloud deployment as the filesystem is ephemeral (data is lost on restart). You will need to migrate to a hosted database such as [Supabase](https://supabase.com) (free tier available).

### Steps

1. **Create a Supabase project** at [supabase.com](https://supabase.com)

2. **Create the tables** in the Supabase SQL Editor:
    ```sql
    CREATE TABLE readings (
        id BIGSERIAL PRIMARY KEY,
        "user" TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        systolic INTEGER NOT NULL,
        diastolic INTEGER NOT NULL,
        pulse INTEGER,
        arm TEXT DEFAULT 'Left',
        position TEXT DEFAULT 'Sitting',
        notes TEXT
    );

    CREATE TABLE medications (
        id BIGSERIAL PRIMARY KEY,
        "user" TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        name TEXT NOT NULL,
        dosage TEXT,
        notes TEXT
    );
    ```

3. **Add secrets** — create `.streamlit/secrets.toml` locally (this file should be in `.gitignore`):
    ```toml
    SUPABASE_URL = "https://your-project.supabase.co"
    SUPABASE_KEY = "your-anon-key"
    ```
    Add the same values in the Streamlit Cloud dashboard under **App settings → Secrets**.

4. **Push to GitHub** and connect the repo in the [Streamlit Cloud dashboard](https://share.streamlit.io).

## .gitignore

Make sure your `.gitignore` includes:
```
blood_pressure.db
blood_pressure.db-shm
blood_pressure.db-wal
.streamlit/secrets.toml
```

## Requirements

- Python 3.8+
- streamlit
- pandas
