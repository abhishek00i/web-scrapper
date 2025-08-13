import requests
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BACKEND_URL = "http://localhost:5001"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    print("Serving home page.")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape", response_class=HTMLResponse)
async def scrape_hotels_post(
    request: Request,
    location: str = Form(...),
    checkin_date: str = Form(...),
    checkout_date: str = Form(...),
    num_adults: int = Form(...),
    num_children: int = Form(...),
    children_ages: str = Form(default="")
):
    print(f"Received scrape request for location: {location}")
    payload = {
        "location": location,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "num_adults": num_adults,
        "num_children": num_children,
        "children_ages": children_ages
    }
    
    response = requests.post(f"{BACKEND_URL}/scrape", data=payload)
    if response.status_code == 200:
        data = response.json()
        hotels = data.get("hotels", [])
        print(f"Received {len(hotels)} hotels from backend.")
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "hotels": hotels,
                "location": location
            }
        )
    else:
        print(f"Backend error: {response.status_code} - {response.text}")
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "hotels": [],
                "location": location,
                "error": f"Failed to scrape: {response.text}"
            }
        )

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI frontend on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)