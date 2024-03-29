# Process buildings from all LADs

import time
import requests
import building_classification as building_classification
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

    # check the required keys are present
    required_keys=['user', 'password', 'url']
    for key in required_keys:
        if key not in settings.keys():
            return 'Error! Settings file is missing a required key: %s' %key

    return settings


def main():
    """Main function
    """
    start_time = time.time()
    timestr = time.strftime("%Y%m%d-%H%M%S")
    start_time2 = time.asctime()
    print("Program starts at: ", start_time2)

    logging.basicConfig(filename='MISTRAL_Classification.log', level=logging.DEBUG)

    usr_settings = import_config()

    # Get a list of LADs from the NISMOD API to iterate over
    #response = requests.get(usr_settings['url']+'/data/boundaries/lads/get_lads?lad_codes=all', auth=(usr_settings['user'], usr_settings['password']))

    #print(response)
    Year = '2011'
    LAD_count = 1

    if LAD_count >= 1:# response.status_code == 200:
        print("LAD data obtained from API")
        #logging.debug('LAD data obtained from API')
        #dataReturned = response.text

        #jsonText = json.loads(dataReturned)
        #Year = "2011"

        #for textLine in jsonText[327:]: # this needs updating/fixing
            # print(textLine)
            #LAD_Code = textLine['lad_code']
        LAD_Code = 'E08000021'

        print("Processing LAD " + str(LAD_count) + ", LAD Code " + LAD_Code + " at " + str(time.asctime()))
        logging.debug("Processing LAD " + str(LAD_count) + ", LAD Code " + LAD_Code + " at " + str(time.asctime()))

        result = building_classification.building_classification(usr_settings, LAD_Code, Year)
        LAD_count += 1

        if result == "Success":
            print("All LADs processed successfully.")
        #break

main()
