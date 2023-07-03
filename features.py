import json
from collections import Counter
import pandas as pd


def extract_features(input_file_path, output_file_path):
    # Load data from input file
    with open(input_file_path) as in_file:
        data = json.load(in_file)

    # Define an empty dictionary to store unique features and their possible values
    feature_set = {}

    # Iterate over each car in data
    for car in data:
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

    # Save the feature_set dictionary to the output file
    with open(output_file_path, 'w') as out_file:
        json.dump(feature_set, out_file, ensure_ascii=False, indent=4)


import json


def modify_calendar_field(input_file_path, output_file_path):
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

    # Save the modified data to the output file
    with open(output_file_path, 'w') as out_file:
        json.dump(data, out_file, ensure_ascii=False, indent=4)


def move_make(input_file_path, output_file_path):
    # Load data from input file
    with open(input_file_path) as in_file:
        data = json.load(in_file)

    # Iterate over each car in data
    for car in data:
        # Check if the car has 'make' field and 'features' field
        if "make" in car and "features" in car:
            # Move the 'make' field to 'features' field
            car['features']['make'] = car['make']
            # Delete the 'make' field from the car
            del car['make']

    # Save the modified data to the output file
    with open(output_file_path, 'w') as out_file:
        json.dump(data, out_file, ensure_ascii=False, indent=4)


def generate_statistics(car_details_path, features_path):
    # Load car details from file
    with open(car_details_path) as car_file:
        car_details = json.load(car_file)

    # Load feature set from file
    with open(features_path) as feature_file:
        feature_set = json.load(feature_file)

    # Initialize a dictionary to store the counts of each feature
    feature_counts = {feature: Counter() for feature in feature_set.keys()}

    # Iterate over each car in data
    for car in car_details:
        if "features" in car:
            # Increment count for each feature present in the car
            for feature, value in car["features"].items():
                if feature in feature_counts:
                    feature_counts[feature][value] += 1

    # Initialize dictionary to store the statistics
    statistics = {}

    # Calculate statistics
    total_cars = len(car_details)
    for feature, counter in feature_counts.items():
        if len(feature_set[feature]) > 1:
            # If a feature has multiple possible values, store percentage for each value
            statistics[feature] = {value: (count / total_cars) * 100 for value, count in counter.items()}
        else:
            # If a feature only has one possible value, store the percentage of cars that have it
            value = feature_set[feature][0]
            statistics[feature] = {
                value: (counter[value] / total_cars) * 100,
                'no ' + value: ((total_cars - counter[value]) / total_cars) * 100
            }

    return statistics


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


def calculate_influence(car_details_path, features_path, output_file_path):
    # Load car details from file
    with open(car_details_path) as car_file:
        car_details = json.load(car_file)

    # Load feature set from file
    with open(features_path) as feature_file:
        feature_set = json.load(feature_file)

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


# Call the function with paths to the input and output files
modify_calendar_field('car_details.json', 'car_details_parsed.json')
move_make('car_details_parsed.json', 'car_details_parsed.json')

# Call the function with paths to the input and output files
extract_features('car_details_parsed.json', 'feature_set.json')

# Call the function with paths to the car details and feature set files
statistics = generate_statistics('car_details_parsed.json', 'feature_set.json')

# Call the function with paths to the car details and feature set files
calculate_influence('car_details_parsed.json', 'feature_set.json', 'output_advanced.html')
