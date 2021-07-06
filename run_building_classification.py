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
    lads = []
    #gors = ['S92000003','W92000004','E12000001','E12000002','E12000003','E12000004','E12000005','E12000006','E12000007','E12000008','E12000009']
    #gors = ['E12000001','E12000002','E12000003','E12000004','E12000005','E12000006','E12000007','E12000008','E12000009']
    gors = ['E12000001','E12000002']

    for gor in gors:
        rstring = 'https://www.nismod.ac.uk/api/data/boundaries/lads_in_gor?gor_codes=%s&export_format=geojson' % (gor)
        response = requests.get(rstring, auth=(usr_settings['user'], usr_settings['password']))
        data = json.loads(response.text)

        for feat in data['features']:
            lads.append(feat['properties']['lad_code'])

    print(len(lads))

    #print(response)
    Year = '2011'
    LAD_count = 1

    #while LAD_count < len(lads):# response.status_code == 200:
    for lad in lads:
        print("LAD data obtained from API")

        LAD_Code = lad

        print("Processing LAD " + str(LAD_count) + ", LAD Code " + LAD_Code + " at " + str(time.asctime()))
        logging.debug("Processing LAD " + str(LAD_count) + ", LAD Code " + LAD_Code + " at " + str(time.asctime()))

        if len(LAD_Code) == 9:
            result = building_classification.building_classification(usr_settings, LAD_Code, Year)
            #pass
        LAD_count += 1


    #if result == "Success":
    #    print("All LADs processed successfully.")
    #break

main()
