## Booking.com Hotel Scraper (FastAPI + Flask + Playwright)

A two-service web app that scrapes hotel listings from Booking.com. The backend uses Playwright (Chromium) and BeautifulSoup to collect data, exposed via a Flask API. The frontend is a FastAPI app that renders a simple UI where users can search and view results.

Important: Respect the Booking.com Terms of Service and robots.txt, and ensure you have permission to scrape any site. This project is for educational purposes only.

### Features
- **Form-based search**: Location, dates, adults, children, and children ages.
- **Headless browser scraping**: Playwright with basic anti-bot evasions.
- **Parsing**: BeautifulSoup to extract hotel name, price, trip duration, and guest details.
- **Frontend UI**: FastAPI + Jinja templates, Tailwind via CDN.
- **JSON API**: Backend endpoint returns structured hotel data.

### Architecture
- **Frontend (FastAPI)**: Serves the UI and calls the backend API.
  - Port: 8000
  - Path: `frontend/app.py`
- **Backend (Flask)**: Performs scraping with Playwright and returns JSON.
  - Port: 5001
  - Path: `backend/scraper.py`

Flow:
1. User submits the form on `/` (frontend).
2. Frontend POSTs the same payload to backend `/scrape`.
3. Backend launches Playwright, navigates to Booking.com search URL, scrapes results, and returns JSON.
4. Frontend renders the results in a table.

### Tech Stack
- Python, FastAPI, Flask
- Playwright (Chromium), BeautifulSoup4
- Jinja2, Tailwind CSS (CDN)

### Project Structure
```
booking-com/
  backend/
    scraper.py            # Flask API + Playwright scraping logic
  frontend/
    app.py                # FastAPI app (UI + backend proxy)
    static/               # Static assets (optional)
    templates/
      index.html          # Search form
      results.html        # Results table
  requirement.txt         # Minimal deps; see Prerequisites for full list
```

### Prerequisites
- Python 3.9+ (3.10 recommended)
- pip
- Playwright browsers (installed after pip step)

Required Python packages (some may not be listed in `requirement.txt`):
- fastapi, uvicorn
- flask
- requests
- beautifulsoup4
- playwright==1.40.0 (or compatible)
- Optional: `undetected-playwright-patch` (if you plan to experiment with extra evasion)

### Setup
1) Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
# If any packages are missing, install them explicitly:
pip install fastapi uvicorn flask requests beautifulsoup4 playwright

# Install Playwright browsers (Chromium)
python -m playwright install chromium
```

2) Configure proxy (optional but often necessary)

The backend has a placeholder HTTP proxy in `backend/scraper.py`:

```python
proxy = {"server": "http://your-proxy-ip:port"}
```

- Replace with a working proxy (e.g., `http://username:password@host:port`).
- To run without a proxy, set an empty string: `{"server": ""}`; the code will skip proxying when empty.

3) Run the services (in two terminals)

Terminal A — backend (Flask):
```bash
cd backend
python scraper.py
```

Terminal B — frontend (FastAPI):
```bash
cd frontend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
# or: python app.py
```

Open the app at:
```
http://localhost:8000
```

### Usage
1. Fill in Location, Check-in, Check-out, Adults, Children, and Children Ages (comma-separated) on the homepage.
2. Submit the form. The frontend will call the backend and render the results.
3. If no results appear, review the Troubleshooting section below.

### Backend API
- URL: `POST http://localhost:5001/scrape`
- Form fields:
  - `location` (str)
  - `checkin_date` (YYYY-MM-DD)
  - `checkout_date` (YYYY-MM-DD)
  - `num_adults` (int)
  - `num_children` (int)
  - `children_ages` (comma-separated ages, e.g. `4,6`)

Example cURL:
```bash
curl -X POST http://localhost:5001/scrape \
  -d location="New York" \
  -d checkin_date=2025-09-01 \
  -d checkout_date=2025-09-05 \
  -d num_adults=2 \
  -d num_children=1 \
  -d children_ages=7
```

Response shape:
```json
{
  "hotels": [
    {
      "name": "Hotel Name",
      "price": "$300",
      "duration": "4 days 4 nights",
      "person_details": "2 adults, 1 children (ages: 7)"
    }
  ]
}
```

### Notes and Limitations
- The scraping logic relies on the current Booking.com DOM. If selectors change, update them in `backend/scraper.py`.
- Headless is set to `False` for easier debugging. You can set `headless=True` once your proxy/browser setup is stable.
- The template includes a "Download CSV" link, but no route is implemented yet. Consider adding a FastAPI route that streams a CSV built from the latest results.

### Troubleshooting
- "No hotel cards found" or empty results:
  - Likely bot detection or network restrictions. Use a reliable proxy. Add delays or interact with the page if needed.
  - Ensure `python -m playwright install chromium` ran successfully.
  - Try increasing wait times in `scrape_hotels` (e.g., `wait_for_timeout`).
- Playwright launch errors on macOS:
  - Ensure Xcode Command Line Tools are installed (`xcode-select --install`).
  - Reinstall browsers: `python -m playwright install chromium`.
- 500 or 4xx from backend:
  - Check terminal logs for both backend and frontend.
  - Verify the backend is on port 5001 and reachable from the frontend.

### Roadmap Ideas
- Add CSV export endpoint to the frontend.
- Add environment-based configuration (ports, proxy, headless mode).
- Implement retries and richer logging/metrics.
- Dockerize both services for easier deployment.

### Legal
This project is provided for educational purposes only. Scraping may be restricted by the target website’s Terms of Service and applicable law. You are solely responsible for how you use this code.


