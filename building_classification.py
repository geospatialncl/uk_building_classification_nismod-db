import requests
from shapely import wkt
from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
import itertools
import json
import logging


def get_buildings(user_settings, year, area_code):
    """Get buildings from NISMOD-DB API
    """
    #queryText = user_settings['url'] + '/data/mastermap/buildings?building_year=' + year + '&scale=lad&area_codes=' + area_code + '&building_use=residential'
    queryText = 'https://www.nismod.ac.uk/api/data/mastermap/buildings?scale=%s&area_codes=%s&building_year=2011' % ('lad', area_code)
    print(queryText)
    response = requests.get(queryText, auth=(user_settings['user'], user_settings['password']))

    # 200 = successful
    i = 0
    if response.status_code == 200:

        jsonText = json.loads(response.text)
        buildingPolys = {}
        buildingAttributes = {}
        print("Loading building polygons from API")

        for textLine in jsonText:

            i += 1
            poly = wkt.loads(textLine['geom'])

            # check the toid is correct
            TOID = str(textLine['toid'])
            if len(TOID) < 16:
                TOID = "000" + TOID

            buildingPolys[TOID] = poly
            buildingAttributes[TOID] = textLine

        return buildingPolys, buildingAttributes, i

    else:
        logging.error("Error reading building data from API. Building query response code is: ", response.status_code)
        print("Error reading building data from API. Building query response code is: ", response.status_code)
        return "Error reading building data from API. Building query response code is: %s" % response.status_code


def get_oas(user_settings, area_code):
    """Get output areas in a LAD
    """
    queryText2 = user_settings['url'] + "/data/boundaries/oas_in_lad?lad_codes=" + area_code

    response = requests.get(queryText2, auth=(user_settings['user'], user_settings['password']))

    i = 0
    # OAPolys = {}
    OA_Attributes = {}
    OANeigh_Dict = {}

    # 200 = successful
    if response.status_code == 200:

        jsonText = json.loads(response.text)

        for textLine in jsonText:
            i += 1
            poly = wkt.loads(textLine['geom'])

            OA_code = str(textLine['oa_code'])
            # OAPolys[OA_code] = poly
            OA_Attributes[OA_code] = textLine
            OANeigh_Dict[OA_code] = textLine['oa_neighbours']

        print(i, " OAs loaded successfully")
        return OA_Attributes, OANeigh_Dict, i

    else:
        logging.error("Error loading OAs from API. OA query response code is: ", response.status_code)
        print("Error loading OAs from API. OA query response code is: ", response.status_code)
        return "Error loading OAs from API. OA query response code is: %s" % response.status_code


def building_classification(user_settings, LAD_Code_to_be_processed, year):
    """
    UK Residential Building Classification using NISMOD API
    -------------------------------------------------------

    This script uses the NISMOD-DB++ API to classify OS Mastermap buildings at local authority district (LAD) scale. The script extracts residential buildings using the API and, using topological properties between buildings and Addressbase points, classifies into one of four residential classes:

    1) Detached
    2) Semi-detached
    3) Terraced
    4) Flat

    There are also Communal dwellings.

    The script assigns a MISTRAL building class and posts the resulting data back to the NISMOD-DB++ database.

    Requires: Shapely, requests, itertools, json.
    """

    # API call - get buildings
    buildingPolys, buildingAttributes, i = get_buildings(user_settings, year, LAD_Code_to_be_processed)
    print(i, " buildings loaded successfully")

    print("Pre-processing OAs...")
    print("")

    # API call - get census output areas
    OA_Attributes, OANeigh_Dict, i = get_oas(user_settings, LAD_Code_to_be_processed)

    print("There are " + str(len(OA_Attributes)) + " OAs in the loaded dictionary.")
    print("There are " + str(len(buildingPolys)) + " buildings in the loaded dictionary.")

    buildingsinOAs = dict((oa, []) for oa in OA_Attributes.keys())

    #
    # Building Polygon Analysis
    #

    buildingTOIDList = buildingAttributes.keys()
    buildingNumResAddPoints = {}

    for building in buildingTOIDList:
        attributesforBuilding = (buildingAttributes[building])
        buildingOA = attributesforBuilding['oa']
        numResAddPoints = (attributesforBuilding['res_count'])
        buildingNumResAddPoints[building] = numResAddPoints
        building_assigned = False

        #Record the buildings in each OA
        for oa in buildingsinOAs.keys():
            if buildingOA == oa:
                buildingsinOAs[oa].append(building)
                building_assigned = True
        if building_assigned is False:
            print('Building ' + str(building) + ' not assigned')

    #
    # Identify the house typology (terrace, semi-detached, detached, flat)
    # Common border to identify house typology (excluding flats) ***WORK***

    print("Processing building topologies")

    sharedBoundariesBuildings = dict((TOID, []) for TOID in buildingTOIDList)   #key: TOID; values: neighbour(s) WITHOUT TERRACES
    total_no_of_Buildings = 0
    OAbuildings = []
    i = 0

    i = 0
    #Get buildings in each OA
    print(len(buildingsinOAs.keys()))
    for key in sorted(buildingsinOAs):

        print('Looking at OA %s' %key)

        total_no_of_Buildings += len(buildingsinOAs[key])

        # here is where I need to add the buildings from the neighbouring OAs
        # buildings in OA of interest
        OAbuildings = buildingsinOAs[key]

        # add buildings from neighbouring OAs
        #print(OANeigh_Dict.keys())
        #print(OANeigh_Dict[key])
        #print(len(OAbuildings))
        for neighbour in OANeigh_Dict[key]:
            OAbuildings += buildingsinOAs[neighbour]
        #print(len(OAbuildings))

        #Create list of buildings in OA and their polygons
        for buildingTOID1, buildingTOID2 in itertools.permutations(OAbuildings, 2):
            i += 1

            buildingPolygon1 = buildingPolys[buildingTOID1]
            buildingPolygon2 = buildingPolys[buildingTOID2]

            if shape(buildingPolygon1).touches(shape(buildingPolygon2)):
                if buildingTOID1 in sharedBoundariesBuildings.keys():
                    if buildingTOID2 in sharedBoundariesBuildings[buildingTOID1]:
                        pass
                    else:
                        sharedBoundariesBuildings[buildingTOID1].append(buildingTOID2)
                else:
                    sharedBoundariesBuildings[buildingTOID1]= buildingTOID2
        i += 1
        if i == 5:
            break
    print('')

    print(str(total_no_of_Buildings) + " buildings in OA")
    print(str(len(OAbuildings)) + " buildings in all OAs")
    logging.debug(str(total_no_of_Buildings) + " buildings in all OAs")
    print('')

    print("Overview of sharedBoundariesBuildings")
    print("Total buildings with neighbours: %s" %(len(sharedBoundariesBuildings)))

    connectedBuildings = {}  #key: TOID; values: neighbour(s) to include TERRACES

    for buildingTOID in sharedBoundariesBuildings.keys():

        buildingstoSearch = []

        buildingstoSearch.extend(sharedBoundariesBuildings[buildingTOID])

        for sBuilding in buildingstoSearch:
            for sBuilding2 in sharedBoundariesBuildings[sBuilding]:
                if sBuilding2 == buildingTOID:
                    pass
                else:
                    if sBuilding2 in buildingstoSearch:
                        pass
                    else:
                        buildingstoSearch.append(sBuilding2)
        connectedBuildings[buildingTOID] = buildingstoSearch


    masterBuildingList = []    #All buildings

    for oa in buildingsinOAs.keys():
        for building in buildingsinOAs[oa]:
            masterBuildingList.append(building)

    print("masterBuildingList: %s" %(len(masterBuildingList)))
    print("connectedBuildings: %s" %(len(connectedBuildings)))

    buildingType = {}     #key: TOID; values: type

    # this is where we actually assign a property to each building
    for eachBuilding in masterBuildingList:
        if str(eachBuilding) in connectedBuildings.keys():
            if len(connectedBuildings[str(eachBuilding)]) >1: # more than one neighbour - must be terraced
                if buildingNumResAddPoints[eachBuilding] > 1:
                    buildingType[str(eachBuilding)] = "Flat_T"
                else:
                    buildingType[str(eachBuilding)] = "Terrace"
            elif len(connectedBuildings[str(eachBuilding)]) == 1:
                if buildingNumResAddPoints[eachBuilding] > 1:
                    buildingType[str(eachBuilding)] = "Flat_SD"
                else:
                    buildingType[str(eachBuilding)] = "Semi-detached" # only one connected building so much be semi-d
            else:
                if buildingNumResAddPoints[eachBuilding] > 1:
                    buildingType[str(eachBuilding)] = "Flat_D"
                else:
                    buildingType[str(eachBuilding)] = "Detached"    #doesn't have any connected buildings so must be detached
        else:
            print('Possible error here')

    print("buildingType: %s" %(len(buildingType)))


    print("Uploading building types")
    OAbuildings = {}
    buildingUpload = {}
    i = 0

    for oa in buildingsinOAs.keys():
            OAbuildings = buildingsinOAs[oa]
            for building in OAbuildings:
                i += 1
                currentBuildingType = buildingType[building]

                buildingUpload[building] = currentBuildingType
                #print(buildingUpload)
                #break
            #break
                if (i % 1000) == 0:
                    #response = requests.post(user_settings['url'] + '/data/mastermap/update_building_class?year=' + year + '&building_class=true', auth=(user_settings['user'], user_settings['password']), data=buildingUpload)
                    buildingUpload = {}


    #response = requests.post(user_settings['url'] + '/data/mastermap/update_building_class?year=' + year + '&building_class=true', auth=(user_settings['user'], user_settings['password']), data=buildingUpload) #Type)
    logging.debug("Building types uploaded for LAD code " + LAD_Code_to_be_processed)
