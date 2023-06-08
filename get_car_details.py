import asyncio
from pyppeteer import launch
import pyppeteer
import json
import logging
import re
import os

# Set up logging
logging.basicConfig(level=logging.INFO)


async def get_car_specific_details(page):
    # Get page content as string
    content = await page.content()

    # Get make and model
    make_model_regex = re.search(r'<!--<div class="slText">(.*?)<br>(.*?)<\/div>-->', content)
    make_model = {'make': make_model_regex.group(1).strip(), 'model': make_model_regex.group(2).strip()} if make_model_regex else {'make': '', 'model': ''}

    # Get longitude and latitude
    location_elem = await page.querySelector('#map')
    location = await page.evaluate('''(element) => {
        return {
            'latitude': element.getAttribute('data-latitude').trim(),
            'longitude': element.getAttribute('data-longitude').trim()
        };
    }''', location_elem)

    # Get features
    features = await page.evaluate('''() => {
        const features_lists = Array.from(document.querySelectorAll('ul.rubrique_option'));
        return features_lists.reduce((features, ul) => {
            const new_features = Array.from(ul.querySelectorAll('li')).reduce((features, li) => {
                const imgElement = li.querySelector('img');
                if (imgElement) {
                    const key = imgElement.src.split('/').pop().split('.')[0].trim();
                    const value = li.querySelector('div:last-child').textContent.trim();
                    features[key] = value;
                }
                return features;
            }, {});
            return { ...features, ...new_features };
        }, {});
    }''')

    # Click on "Mehr Kommentare" button until it becomes hidden
    more_button_selector = '.more_comment span'
    while True:
        try:
            more_button_visible = await page.querySelector(more_button_selector)
            if more_button_visible:
                await page.click(more_button_selector)
                await page.waitFor(1000)  # wait for a while to let the button hide
            else:
                break
        except pyppeteer.errors.ElementHandleError:
            break

    # Get reviews
    reviews = await page.evaluate('''() => {
        const review_elements = Array.from(document.querySelectorAll('ul.rubrique_coment .rub_coment_date'));
        return review_elements.map(elem => elem.textContent.trim());
    }''')

    return {**make_model, **location, 'features': features, 'reviews': reviews}


async def check_and_get_car_details(browser, car_data):
    # Load existing details data
    if os.path.exists('car_details.json'):
        with open('car_details.json', 'r') as f:
            car_details_data = json.load(f)
    else:
        car_details_data = []

    for car in car_data:
        # If car details not already fetched
        if not any(car_detail['url'] == car['url'] for car_detail in car_details_data):
            logging.info(f"Fetching details for car at url {car['url']}")
            page = await browser.newPage()
            await page.goto(car['url'])
            car_details = await get_car_specific_details(page)
            car_details['url'] = car['url']
            car_details_data.append(car_details)
            # Save after every fetch
            with open('car_details.json', 'w') as f:
                json.dump(car_details_data, f, ensure_ascii=False)
            logging.info(f"Finished fetching details for car at url {car['url']}")
            await page.close()
        else:
            logging.info(f"Details for car at url {car['url']} already fetched")

    return car_details_data


async def main():
    # Load URLs from car_data_zurich.json
    with open('car_data_zurich.json', 'r') as f:
        car_data = json.load(f)

    # Launch the browser
    logging.info("Launching browser...")
    browser = await launch({'headless': True})

    # Get car details
    logging.info("Starting to fetch car details...")
    car_details = await check_and_get_car_details(browser, car_data)

    # Close the browser
    logging.info("Closing browser...")
    await browser.close()

    # Print to verify the function works
    print(car_details)


# Run the main function
asyncio.get_event_loop().run_until_complete(main())