from flask import Flask, request, jsonify
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class BookingScraper:
    def __init__(self):
        self.base_url = "https://www.booking.com"
        self.hotels_data = []

    async def init_browser(self, playwright):
        print("Initializing browser...")
        # Use a free proxy (replace with a working one, e.g., from https://free-proxy-list.net/)
        proxy = {"server": "http://your-proxy-ip:port"}  # Example: "http://123.456.78.90:8080"
        try:
            browser = await playwright.chromium.launch(
                headless=False,  # Set to False for debugging; use True with a working proxy
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-blink-features=AutomationControlled'
                ],
                proxy=proxy if proxy["server"] else None
            )
            print("Browser launched successfully.")
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale="en-US",
                java_script_enabled=True
            )
            await context.add_init_script(script="Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
            print("Context created successfully.")
            return browser, context
        except Exception as e:
            logger.error(f"Browser initialization failed: {e}")
            raise

    def format_duration(self, checkin_date: str, checkout_date: str) -> str:
        print(f"Formatting duration: {checkin_date} to {checkout_date}")
        try:
            checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
            checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
            delta = checkout - checkin
            total_days = delta.days
            nights = total_days
            if total_days == 0:
                return "Same day stay"
            days_text = "day" if total_days == 1 else "days"
            nights_text = "night" if nights == 1 else "nights"
            return f"{total_days} {days_text} {nights} {nights_text}"
        except ValueError as e:
            print(f"Error formatting duration: {e}")
            return "Invalid date format"

    async def scrape_hotels(self, location: str, checkin_date: str, checkout_date: str, num_adults: int, num_children: int, children_ages: List[int]) -> List[Dict]:
        self.hotels_data = []  # Reset
        async with async_playwright() as playwright:
            browser, context = await self.init_browser(playwright)
            page = await context.new_page()

            try:
                location_encoded = location.replace(' ', '+')
                children_ages_str = '&'.join([f'age={age}' for age in children_ages])
                search_url = (
                    f"{self.base_url}/searchresults.html?"
                    f"ss={location_encoded}&"
                    f"ssne={location_encoded}&"
                    f"ssne_untouched={location_encoded}&"
                    f"label=gen173nr-1FCAEoggI46AdIM1gEaGyIAQGYATG4AQfIAQ3YAQHoAQH4AQKIAgGoAgO4AqPUlcMGwAIB0gIkNWZlYWUyZjQtNjU3Yy00Njg4LTk5NmEtMmY2MGIxZDBiNmM12AIF4AIB&"
                    f"aid=304142&"
                    f"lang=en-us&"
                    f"sb=1&"
                    f"src_elem=sb&"
                    f"src=index&"
                    f"checkin={checkin_date}&"
                    f"checkout={checkout_date}&"
                    f"group_adults={num_adults}&"
                    f"no_rooms=1&"
                    f"group_children={num_children}&"
                    f"{children_ages_str}"
                )
                logger.info(f"Navigating to search URL: {search_url}")

                await page.goto(search_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                hotel_cards = soup.select("div[data-testid='property-card']")
                if not hotel_cards:
                    logger.warning("No hotel cards found. Possible bot detection or empty results.")
                    return []

                for card in hotel_cards:
                    hotel = {}
                    try:
                        name_elem = card.select_one("div[data-testid='title']")
                        hotel['name'] = name_elem.text.strip() if name_elem else "N/A"
                        price_elem = card.select_one("span[data-testid='price-and-discounted-price']")
                        hotel['price'] = price_elem.text.strip() if price_elem else "N/A"
                        hotel['duration'] = self.format_duration(checkin_date, checkout_date)
                        person_details = f"{num_adults} adults"
                        if num_children > 0:
                            person_details += f", {num_children} children (ages: {', '.join(map(str, children_ages))})"
                        hotel['person_details'] = person_details
                        self.hotels_data.append(hotel)
                    except Exception as e:
                        logger.error(f"Error parsing hotel card: {e}")
                        continue

                logger.info(f"Scraped {len(self.hotels_data)} hotels")
                return self.hotels_data

            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                return []
            finally:
                await browser.close()

@app.route('/scrape', methods=['POST'])
def scrape_hotels():
    location = request.form.get('location')
    checkin_date = request.form.get('checkin_date')
    checkout_date = request.form.get('checkout_date')
    num_adults = int(request.form.get('num_adults', 1))
    num_children = int(request.form.get('num_children', 0))
    children_ages_str = request.form.get('children_ages', '')
    children_ages = [int(age) for age in children_ages_str.split(',') if age.strip().isdigit()] if children_ages_str else []

    if not all([location, checkin_date, checkout_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    scraper = BookingScraper()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    hotels = loop.run_until_complete(scraper.scrape_hotels(location, checkin_date, checkout_date, num_adults, num_children, children_ages))
    loop.close()
    return jsonify({"hotels": hotels})

if __name__ == "__main__":
    print("Starting scraper server on port 5000...")
    app.run(host='0.0.0.0', port=5001)