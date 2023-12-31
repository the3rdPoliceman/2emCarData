#!/bin/bash

# define arrays for urls and output filenames
urls=(
'https://de.2em.ch/autovermietung?adresse=Bern%2C+Schweiz&search=Suche&date_depart=24%2F06%2F2023&date_retour=26%2F06%2F2023&state_am=10%3A00&state_pm=13%3A00&vehicule=auto&latitude=46.9479739&longitude=7.4474468&resetsearch=1'
'https://de.2em.ch/autovermietung?adresse=Basel%2C+Schweiz&search=Suche&date_depart=24%2F06%2F2023&date_retour=26%2F06%2F2023&state_am=09%3A00&state_pm=14%3A00&vehicule=auto&latitude=47.5595986&longitude=7.5885761&resetsearch=1'
'https://de.2em.ch/autovermietung?adresse=Lausanne%2C+Schweiz&search=Suche&date_depart=24%2F06%2F2023&date_retour=26%2F06%2F2023&state_am=10%3A00&state_pm=11%3A00&vehicule=auto&latitude=46.5196535&longitude=6.6322734&resetsearch=1'
'https://de.2em.ch/autovermietung?adresse=Gen%C3%A8ve%2C+Schweiz&search=Suche&date_depart=23%2F06%2F2023&date_retour=25%2F06%2F2023&state_am=09%3A00&state_pm=09%3A00&vehicule=auto&latitude=46.2043907&longitude=6.1431577&resetsearch=1'
'https://de.2em.ch/autovermietung?adresse=Z%C3%BCrich%2C+Schweiz&search=Suche&date_depart=24%2F06%2F2023&date_retour=26%2F06%2F2023&state_am=09%3A00&state_pm=16%3A00&vehicule=auto&latitude=47.3768866&longitude=8.541694&resetsearch=1'
)

files=(
'V1_Results/car_data_bern.json'
'V1_Results/car_data_basel.json'
'V1_Results/car_data_lausanne.json'
'V1_Results/car_data_geneva.json'
'V1_Results/car_data_zurich.json'
)

# loop over urls
for i in "${!urls[@]}"; do
    url=${urls[i]}
    file=${files[i]}
    python3 scrape_car_basic_data.py -u "$url" -o "$file"
done
