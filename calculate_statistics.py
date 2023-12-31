import json
from collections import Counter
import pandas as pd
import json


OUTPUT_ADVANCED_HTML = 'V1_Results/output_advanced.html'
FEATURE_SET_JSON = 'V1_Results/feature_set.json'
CAR_DETAILS_PARSED_JSON = 'V1_Results/car_details_parsed.json'
ORIGINAL_CAR_DETAILS_JSON = 'V1_Results/car_details.json'


def modify_calendar_field_and_move_make(input_file_path):
    # Load data from input file
    with open(input_file_path) as in_file:
        data = json.load(in_file)

    # Iterate over each car in data
    for car in data:
        # Check if the car has features and if 'calendar' field is in the features
        if "features" in car and 'calendar' in car['features']:
            # Get the 'calendar' field
            calendar = car['features']['calendar']
            # Extract the year from the 'calendar' field
            year = calendar.split('.')[-1]
            # Replace the 'calendar' field with the 'year' field
            del car['features']['calendar']
            car['features']['year'] = year

        # Check if the car has 'make' field and 'features' field
        if "make" in car and "features" in car:
            # Move the 'make' field to 'features' field
            car['features']['make'] = car['make']
            # Delete the 'make' field from the car
            del car['make']

    return data


def generate_complete_feature_set(car_data):
    # Define an empty dictionary to store unique features and their possible values
    feature_set = {}

    # Iterate over each car in data
    for car in car_data:
        # Check if the car has features
        if "features" in car:
            # Iterate over each feature in the car
            for feature, value in car["features"].items():
                # If the feature is already in the feature_set dictionary
                if feature in feature_set:
                    # Add the value to the set of possible values for that feature
                    feature_set[feature].add(value)
                else:
                    # If the feature is not in the feature_set dictionary, add it
                    feature_set[feature] = {value}

    # Convert the sets to lists (for JSON serialization)
    for feature, values in feature_set.items():
        feature_set[feature] = list(values)

    return feature_set


def calculate_feature_stats(car_details, feature, options):
    # Count the total number of rentals and the number of rentals for cars with each option
    total_rentals = sum(len(car['reviews']) for car in car_details)
    option_counts = Counter()
    option_rentals = Counter()


    for car in car_details:
        if "features" in car and feature in car["features"]:
            option = car["features"][feature]
            option_counts[option] += 1
            option_rentals[option] += len(car['reviews'])

    # Calculate statistics
    total_cars = len(car_details)
    stats = {}
    for option in options:
        option_proportion = option_counts[option] / total_cars
        rental_proportion = option_rentals[option] / total_rentals if total_rentals > 0 else 0
        influence_ratio = rental_proportion / option_proportion if option_proportion > 0 else 0

        stats[option] = {
            'Feature Proportion': option_proportion * 100,
            'Rental Proportion': rental_proportion * 100,
            'Influence Ratio': influence_ratio
        }

    return stats


def calculate_influence(car_details, feature_set, output_file_path):
    # Calculate statistics for each feature
    multi_option_stats = {}
    single_option_stats = {}
    for feature, options in feature_set.items():
        feature_stats = calculate_feature_stats(car_details, feature, options)
        if len(options) > 1:
            multi_option_stats[feature] = feature_stats
        else:
            single_option_stats.update(feature_stats)

    # Write the DataFrames to an HTML file
    with open(output_file_path, 'w') as f:
        f.write("<h1>Yes/No Features:</h1>\n")
        df_single = pd.DataFrame(single_option_stats).T
        df_single = df_single[['Feature Proportion', 'Rental Proportion', 'Influence Ratio']]
        df_single = df_single.sort_values('Influence Ratio', ascending=False)
        f.write(df_single.to_html())

        for feature, feature_stats in multi_option_stats.items():
            f.write(f"<h1>{feature}:</h1>\n")
            df_multi = pd.DataFrame(feature_stats).T
            df_multi = df_multi[['Feature Proportion', 'Rental Proportion', 'Influence Ratio']]
            df_multi = df_multi.sort_values('Influence Ratio', ascending=False)
            f.write(df_multi.to_html())


# update overall car data and generate a complete feature set
updated_car_details = modify_calendar_field_and_move_make(ORIGINAL_CAR_DETAILS_JSON)
complete_feature_set = generate_complete_feature_set(updated_car_details)
calculate_influence(updated_car_details, complete_feature_set, OUTPUT_ADVANCED_HTML)

# for each region, generate statistics and output files
car_regions = ["basel", "bern", "geneva", "lausanne", "zurich", "test"]

for region in car_regions:
    region_car_detail_file = "V1_Results/car_detail_" + region + ".json"
    region_output_file = "V1_Results/output_advanced_" + region + ".html"

    region_car_details_updated = modify_calendar_field_and_move_make(region_car_detail_file)
    calculate_influence(region_car_details_updated, complete_feature_set, region_output_file)

