# Rural Travel Co-op prototype

Separate backend (FastAPI) and frontend (Streamlit). All trips, operators and fares are made up.
Operator links go to example.com.

    repo/
      backend/   FastAPI service: /health, /cities, /trips (done), /clicks and /members (to build)
      frontend/  Streamlit app that calls the backend

## Run locally (two terminals)
    cd backend && pip install -r requirements.txt && uvicorn main:app --reload
    cd frontend && pip install -r requirements.txt && streamlit run app.py
Backend docs open at http://localhost:8000/docs. The frontend uses http://localhost:8000 by default.

## Deploy (free)
Backend on Render:
1. render.com, New, Web Service, connect this GitHub repository.
2. Root directory: backend. Build command: pip install -r requirements.txt
3. Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
4. Copy the service URL when it is live (the first request after idle can take about a minute).

Frontend on Streamlit Community Cloud:
1. share.streamlit.io, New app, choose this repository.
2. Main file path: frontend/app.py
3. Advanced settings, Secrets: BACKEND_URL = "https://your-render-url.onrender.com"
4. Deploy.

## To build
- Day 2: store trips in SQLite and improve /trips
- Day 3: filters and sorting on the results screen
- Day 4: /clicks endpoint and click report (SQLite)
- Day 5: /members endpoint, then test the whole flow
