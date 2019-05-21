import requests
import shapely
import shapely.wkt
from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
import itertools
import json
import logging


def building_classification(user_settings, LAD_Code_to_be_processed, year):
    ### Classification of buildings from OSMM data in NISMOD-DB++

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

    ## API call

    queryText = user_settings['url']+'/data/mastermap/buildings/get_buildings?building_year=' + year + '&scale=lad&area_codes=' + LAD_Code_to_be_processed  +'&building_use=residential'

    response = requests.get(queryText, auth=(user_settings['user'], user_settings['password']))

    #200 = successful
    i = 0
    if response.status_code == 200:

        #dataReturned = response.text #gets data records returned from API
        #print('Returned data is: ', dataReturned)

        jsonText = json.loads(response.text)
        buildingPolys = {}
        buildingAttributes = {}
        print("Loading building polygons from API")

        for textLine in jsonText:

            #print(i, 'TOID: ', textLine['toid_number'], ' and Building Class: ', textLine['building_class'])
            #print(textLine)
            i += 1
            poly = shapely.wkt.loads(textLine['geom'])
            TOID = str(textLine['toid'])
            if len(TOID) < 16:
                    TOID = "000" + TOID
            buildingPolys[TOID] = poly
            buildingAttributes[TOID] = textLine
    else:
        print ("Error reading building data from API. Building query response code is: ", response.status_code)
        logging.error("Error reading building data from API. Building query response code is: ", response.status_code)

    print(i, " buildings loaded successfully")

    print("Pre-processing OAs...")
    print("")

    queryText2 = user_settings['url']+"/data/boundaries/oas_in_lad?lad_codes=" + LAD_Code_to_be_processed

    response2 = requests.get(queryText2, auth=(user_settings['user'],user_settings['password']))

    i = 0
    #OAPolys = {}
    OA_Attributes = {}
    OANeigh_Dict = {}

     #200 = successful
    if response2.status_code == 200:

        #dataReturned = response2.text #gets data records returned from API

        jsonText = json.loads(response2.text)


        print("Loading OA polygons from API")


        for textLine in jsonText:

            #print(i, 'TOID: ', textLine['toid_number'], ' and Building Class: ', textLine['building_class'])
            #print('Line', i, textLine)
            i += 1
            poly = shapely.wkt.loads(textLine['geom'])
            #print (textLine)
            OA_code = str(textLine['oa_code'])
            #OAPolys[OA_code] = poly
            OA_Attributes[OA_code] = textLine
            OANeigh_Dict[OA_code] = textLine['oa_neighbours']
            #print ("OA " + OA_code + " has neighbours " + str(OANeigh_Dict[OA_code]))
        print(i, " OAs loaded successfully")
    else:
        print("Error loading OAs from API. OA query response code is: ", response2.status_code)
        logging.error("Error loading OAs from API. OA query response code is: ", response.status_code)

    print("There are " + str(len(OA_Attributes)) + " OAs in the loaded dictionary.")
    print("There are " + str(len(buildingPolys)) + " buildings in the loaded dictionary.")

    buildingsinOAs = dict((oa, []) for oa in OA_Attributes.keys())

    #
    # Building Polygon Analysis
    #

    buildingTOIDList = buildingAttributes.keys()
    #buildingsResClass = {}
    buildingNumResAddPoints = {}

    for building in buildingTOIDList:
        attributesforBuilding = (buildingAttributes[building])
        buildingOA = attributesforBuilding['oa']
        numResAddPoints = (attributesforBuilding['res_count'])
        buildingNumResAddPoints[building] = numResAddPoints
        building_assigned = False
        #Record the buildings in each OA
        for oa in buildingsinOAs.keys():
            if  buildingOA == oa:
                buildingsinOAs[oa].append(building)
                building_assigned = True
        if building_assigned == False:
            print('Building ' + str(building) + ' not assigned')


    #print ("buildingsinOAs has: %s members" %(len(buildingsinOAs)))
    # print ("Overview of buildingsinOAs")


    #
    # Identify the house typology (terrace, semi-detached, detached, flat)
    # Common border to identify house typology (excluding flats) ***WORK***

    print("Processing building topologies")

    sharedBoundariesBuildings = dict((TOID, []) for TOID in buildingTOIDList)   #key: TOID; values: neighbour(s) WITHOUT TERRACES
    #total_buildings_in_OA = 0
    total_no_of_Buildings: int = 0
    OAbuildings = []
    i = 0


    #Get buildings in each OA
    for key in sorted(buildingsinOAs):
        #print ("OA = %s has: %s houses" %(key, len(buildingsinOAs[key])))
        total_no_of_Buildings += len(buildingsinOAs[key])
        OAbuildings = buildingsinOAs[key]

        #Create list of buildings in OA and their polygons
        for buildingTOID1, buildingTOID2 in itertools.permutations(OAbuildings, 2):
            i += 1
            #if (i % 1000) == 0:
                #print (str(i) + ": " + str(key))

            buildingPolygon1 = buildingPolys[buildingTOID1]
            buildingPolygon2 = buildingPolys[buildingTOID2]
            #attributesforBuilding1 = (buildingAttributes[buildingTOID1])
            #attributesforBuilding2 = (buildingAttributes[buildingTOID2])

            if shape(buildingPolygon1).touches(shape(buildingPolygon2)):
                if buildingTOID1 in sharedBoundariesBuildings.keys():
                    if buildingTOID2 in sharedBoundariesBuildings[buildingTOID1]:
                        pass
                    else:
                        sharedBoundariesBuildings[buildingTOID1].append(buildingTOID2)
                else:
                    sharedBoundariesBuildings[buildingTOID1]= buildingTOID2
    print('')

    print(str(total_no_of_Buildings) + " buildings in all OAs")
    logging.debug(str(total_no_of_Buildings) + " buildings in all OAs")
    print('')

    print("Overview of sharedBoundariesBuildings")
    print("Total buildings with neighbours: %s" %(len(sharedBoundariesBuildings)))

    #for key in sorted(sharedBoundariesBuildings)[:100]:
            #print ("%s touches: %s" %(key, sharedBoundariesBuildings[key]))
    print("")

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

    #print ("Overview of connectedBuildings")

    #for key in sorted(connectedBuildings)[:2]:
    #    print ("House %s is in the same block of to: %s" %(key, connectedBuildings[key]))

    masterBuildingList = []    #All buildings

    for oa in buildingsinOAs.keys():
        for building in buildingsinOAs[oa]:
            masterBuildingList.append(building)

    print("masterBuildingList: %s" %(len(masterBuildingList)))
    print("connectedBuildings: %s" %(len(connectedBuildings)))

    buildingType = {}     #key: TOID; values: type

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
                    #print("Found a detached!")

    print("Overview of buildingType")

    for key in sorted(buildingType)[:10]:
        print("Building %s is: %s" %(key, buildingType[key]))

    print("buildingType: %s" %(len(buildingType)))


    # Determine number of addresses in building type to identify FlatD, FlatSD, FlatTerr

    print("Uploading building types")

    OAbuildings = {}
    buildingUpload = {}
    i = 0

    for oa in buildingsinOAs.keys():
            OAbuildings = buildingsinOAs[oa]
            for building in OAbuildings:
                i += 1
                currentBuildingType = buildingType[building]
                #uploadStr = {str(building):str(currentBuildingType)}
                #print (uploadStr)
                buildingUpload[building] = currentBuildingType
                if (i % 1000) == 0:
                    response = requests.post(user_settings['url'] + '/data/mastermap/update_building_class?year=' + year + '&building_class=true', auth=(user_settings['user'], user_settings['password']), data=buildingUpload) #Type)
                    buildingUpload = {}

    response = requests.post(user_settings['url'] + '/data/mastermap/update_building_class?year=' + year + '&building_class=true', auth=(user_settings['user'], user_settings['password']), data=buildingUpload) #Type)
    logging.debug("Building types uploaded for LAD code " + LAD_Code_to_be_processed)
