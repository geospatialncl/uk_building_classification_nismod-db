# uk_building_classification_nismod-db
Classification of UK Mastermap buildings using the NISMOD-DB++ API and geometric properties.

UK Residential Building Classification using NISMOD API
-------------------------------------------

This script uses the NISMOD-DB++ API to classify OS Mastermap buildings at local authority district (LAD) scale. The script extracts residential buildings using the API and, using topological properties between buildings and Addressbase points, classifies into one of four residential classes:

1) Detached
2) Semi-detached
3) Terraced
4) Flat

There are also Communal dwellings.

The script assigns a MISTRAL building class and posts the resulting data back to the NISMOD-DB++ database.


init.txt
-------------------------------------------
The script requires a 'init.txt' file to be located in the same directory. This should contain details for connecting to the NISOMD-DB++ API and required there to be three keys, user, password and url. It should look as below:
user="example_user"
password="eg_password"
url="API url"


Dependencies
-------------------------------------------
shapely, requests, itertools, json
