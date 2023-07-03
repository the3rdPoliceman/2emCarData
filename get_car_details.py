import argparse
import asyncio
from pyppeteer import launch
import pyppeteer
import json
import logging
import re
import os
import time

# Set up logging
logging.basicConfig(level=logging.INFO)


async def get_car_specific_details(page):
    # Get page content as string
    content = await page.content()

    # Get make and model
    make_model_regex = re.search(r'<!--<div class="slText">(.*?)<br>(.*?)<\/div>-->', content)
    if make_model_regex:
        make_model = {'make': make_model_regex.group(1).strip(), 'model': make_model_regex.group(2).strip()}
    else:
        logging.warning("Failed to find make and model of the car.")
        make_model = {'make': '', 'model': ''}

    # Get longitude and latitude
    location_elem = await page.querySelector('#map')
    if location_elem is not None:
        location = await page.evaluate('''(element) => {
            return {
                'latitude': element.getAttribute('data-latitude').trim(),
                'longitude': element.getAttribute('data-longitude').trim()
            };
        }''', location_elem)
    else:
        logging.warning("Failed to find location of the car.")
        location = {'latitude': '', 'longitude': ''}

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
    if features is None:
        logging.warning("Failed to find features of the car.")
        features = {}

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
    if reviews is None:
        logging.warning("Failed to find reviews of the car.")
        reviews = []

    return {**make_model, **location, 'features': features, 'reviews': reviews}



async def check_and_get_car_details(browser, car_data, output_file, all_cars_file):
    # Load existing details data
    car_details_data = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            car_details_data = json.load(f)
    all_cars_data = []
    if os.path.exists(all_cars_file):
        with open(all_cars_file, 'r') as f:
            all_cars_data = json.load(f)

    for car in car_data:
        # Check if car details already fetched
        existing_data = [car_detail for car_detail in all_cars_data if car_detail['url'] == car['url']]
        if existing_data:
            logging.info(f"Details for car at url {car['url']} already fetched")
            car_details_data.append(existing_data[0])
            continue

        # If car details not already fetched, fetch with retries - only 1 retry for now
        for _ in range(1):
            try:
                logging.info(f"Fetching details for car at url {car['url']}")
                page = await browser.newPage()
                await page.goto(car['url'])
                await page.waitForSelector('body')  # Ensure page is fully loaded
                car_details = await get_car_specific_details(page)
                car_details['url'] = car['url']
                car_details_data.append(car_details)
                all_cars_data.append(car_details)

                # Save after every fetch
                with open(output_file, 'w') as f:
                    json.dump(car_details_data, f, ensure_ascii=False)
                with open(all_cars_file, 'w') as f:
                    json.dump(all_cars_data, f, ensure_ascii=False)
                logging.info(f"Finished fetching details for car at url {car['url']}")
                await page.close()
                break
            except Exception as e:
                logging.warning(f"Failed to fetch details for car at url {car['url']} due to {e}")
                time.sleep(2)

    return car_details_data


async def main(source_file, output_file, all_cars_file):
    # Load URLs from source file
    with open(source_file, 'r') as f:
        car_data = json.load(f)

    # Launch the browser
    logging.info("Launching browser...")
    browser = await launch({'headless': True})

    # Get car details
    logging.info("Starting to fetch car details...")
    car_details = await check_and_get_car_details(browser, car_data, output_file, all_cars_file)

    # Close the browser
    logging.info("Closing browser...")
    await browser.close()

    # Print to verify the function works
    print(car_details)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape car details.')
    parser.add_argument('source_file', help='The JSON file containing car data.')
    parser.add_argument('output_file', help='The JSON file to output car details to.')
    parser.add_argument('all_cars_file', help='The JSON file containing all car details ever fetched.')
    args = parser.parse_args()

    # Run the main function
    asyncio.get_event_loop().run_until_complete(main(args.source_file, args.output_file, args.all_cars_file))
