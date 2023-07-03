#!/bin/bash

# Define python script path
python_script="get_car_details.py"

# Define all cars file
all_cars_file="car_detail_all.json"

# Define cities
cities=("basel" "bern" "geneva" "lausanne" "luzern" "zurich")

# Loop over cities and run python script for each
for city in "${cities[@]}"; do
    source_file="car_data_${city}.json"
    output_file="car_detail_${city}.json"

    # Run python script with correct arguments
    python3 $python_script $source_file $output_file $all_cars_file
done
