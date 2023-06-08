import asyncio
from pyppeteer import launch
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

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
    url = "https://de.2em.ch/autovermietung?adresse=Gen%C3%A8ve%2C+Schweiz&search=Suche&date_depart=23%2F06%2F2023&date_retour=25%2F06%2F2023&state_am=09%3A00&state_pm=09%3A00&vehicule=auto&latitude=46.2043907&longitude=6.1431577&resetsearch=1"
    page, browser = await get_page_content(url)
    await click_load_more_button(page)
    cars = await get_car_details(page)
    await browser.close()

    logging.info('Writing car details to JSON file...')
    with open('car_data.json', 'w') as file:
        json.dump(cars, file)
    logging.info('Done.')

# Run the main function
asyncio.get_event_loop().run_until_complete(main())
