# Process buildings from all LADs

import time
import requests
import building_classification as building_classification
import sys
import logging
import json


def import_config():
    """Import the user config settings from file
    """
    # open file
    f = open('init.txt', 'r')

    # create a dictionary and read in data
    settings = {}
    for line in f.readlines():
        settings[line.split('=')[0].strip().replace('"',"")] = line.split('=')[1].split('#')[0].strip().replace('"',"")

    return settings


start_time = time.time()
timestr = time.strftime("%Y%m%d-%H%M%S")
start_time2 = time.asctime()
print("Program starts at: ", start_time2)

logging.basicConfig(filename='MISTRAL_Classification.log', level=logging.DEBUG)

usr_settings = import_config()

# Get a list of LADs from the NISMOD API to iterate over
response = requests.get(usr_settings['url']+'/data/boundaries/lads/get_lads?lad_codes=all', auth=(usr_settings['user'], usr_settings['password']))

print(response)
# result = MISTRAL_Residential_Building_Classify('E08000025')

LAD_count = 1

if response.status_code == 200:
    print("LAD data obtained from API")
    logging.debug('LAD data obtained from API')
    dataReturned = response.text

    jsonText = json.loads(dataReturned)
    Year = "2011"

    for textLine in jsonText[327:]:
        # print(textLine)
        LAD_Code = textLine['lad_code']

        print("Processing LAD " + str(LAD_count) + ", LAD Code " + LAD_Code + " at " + str(time.asctime()))
        logging.debug("Processing LAD " + str(LAD_count) + ", LAD Code " + LAD_Code + " at " + str(time.asctime()))

        result = building_classification.building_classification(usr_settings, LAD_Code, Year)
        LAD_count += 1

        if result == "Success":
            print("All LADs processed successfully.")
