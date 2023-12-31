import asyncio
from pyppeteer import launch
import json
import logging
import argparse
import time
from pyppeteer.errors import TimeoutError

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up argument parser
parser = argparse.ArgumentParser(description="Web scraping script")
parser.add_argument('-u', '--url', help='URL to scrape', required=True)
parser.add_argument('-o', '--output', help='Output JSON file', default='car_data.json')
args = parser.parse_args()


async def get_page_content(url):
    logging.info('Launching browser...')
    # Launch the browser
    browser = await launch()
    # Create a new page
    page = await browser.newPage()
    # Navigate to the url
    await page.goto(url)
    logging.info(f'Navigated to {url}')
    return page, browser


async def click_load_more_button(page):
    more_button_selector = '.more-cars'
    load_more_button_selector = '.more-cars .loadmorecars'

    retries = 0
    while retries < 3:
        try:
            # Check if the "more" button is visible
            is_visible = await page.evaluate('''(selector) => {
                const elem = document.querySelector(selector);
                const style = window.getComputedStyle(elem);
                return style.display !== 'none';
            }''', more_button_selector)

            # While the "more" button is visible, click it
            while is_visible:
                logging.info('Clicking "load more" button...')
                # Click the "load more" button
                await page.click(load_more_button_selector)
                # Wait for the page to load
                await asyncio.sleep(2)

                # Check again if the "more" button is visible
                is_visible = await page.evaluate('''(selector) => {
                    const elem = document.querySelector(selector);
                    const style = window.getComputedStyle(elem);
                    return style.display !== 'none';
                }''', more_button_selector)

            break
        except TimeoutError:
            if retries < 3:
                logging.info('Timeout error, waiting for 30 seconds before retry...')
                retries += 1
                time.sleep(30)
                continue
            else:
                logging.error('Reached maximum retry attempts.')
                raise


async def get_car_details(page):
    logging.info('Extracting car details...')
    cars = []
    car_elements = await page.querySelectorAll('.result_car')

    for car in car_elements:
        title_element = await car.querySelector('.car-picture')
        title = await page.evaluate('(element) => element.title', title_element)
        url = await page.evaluate('(element) => element.href', title_element)
        cars.append({'title': title, 'url': url})

    logging.info(f'Extracted details for {len(cars)} cars.')
    return cars


async def main():
    url = args.url
    output_file = args.output
    page, browser = await get_page_content(url)
    await click_load_more_button(page)
    cars = await get_car_details(page)
    await browser.close()

    logging.info('Writing car details to JSON file...')
    with open(output_file, 'w') as file:
        json.dump(cars, file)
    logging.info('Done.')


# Run the main function
asyncio.get_event_loop().run_until_complete(main())
