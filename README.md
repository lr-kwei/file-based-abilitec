# abilitecapi

# ACTIVATE YOUR VIRTUAL ENVIRONMENT BEFORE RUNNING ANYTHING FOR PYTHON 3
# source /home/kevin_wei_liveramp_com/file-based-abilitec/py3venv/bin/activate

#DONT FORGET TO UPDATE THE CREDS AND VERIFY STAGING VS PRODUCTION

#Directions on how to make your own virtual env
mkdir py3venv
pip3 install virtualenv
python3 -m venv /path/to/virtualenvironment/directory


#Passing in a file config via file

There are two ways you can pass a file configuration (mapping columns to audience keys, headers, and touchpoint types) to the application. By default, the app will prompt you to map AKs, headers and touchpoint types to column IDs. You can also pass in those mappings via a json file. 

For each item to be mapped _via app prompt_, pass the zero-indexed column number corresponding to that item AS AN INT OR QUOTED STRING. If that item does not exist, press enter. 

For each item to be mapped _in the config json_, pass the zero-indexed column number corresponding to that item AS A QUOTED STRING. If that item does not exist, insert 'N/A' instead (do not leave it blank). Then call the script with the 'input_param_file' parameter with the path of the json mapping file.

For example:

> /../../file_config.json

{   
    "fileFormat": 
        {        
        "ak": "0",
        "header": "y",
        "dl": ","
        },
    "touchPointColumns": 
        { 
        "firstName": "N/A", 
        "middleName": "N/A", 
        "lastName": "N/A", 
        "generationalSuffix": "N/A", 
        "name": "N/A", 
        "primaryNumber": "N/A", 
        "preDirectional": "N/A", 
        "street": "N/A", 
        "streetSuffix": "N/A", 
        "postDirectional": "N/A", 
        "unitDesignator": "N/A", 
        "secondaryNumber": "N/A", 
        "streetAddress": "N/A", 
        "city": "N/A", 
        "state": "N/A",
        "zipCode": "N/A", 
        "email": "1", 
        "emailMD5": "N/A",
        "phone": "N/A"
        }, 
    "endpointOptions":
        {
        "limit": "1",
        "matchLevel": "default"
        },   
    "outputOptions":
        {        
        "insights: "y",
        "households": "y"
        },
    "personID": "docID",
    "passThroughColumns":
        { 
        "gender": "1",
        "column2": "N/A"
        }
}

`python -c 'from callAbiliTecwithFile import *; appendFile("/../../file_to_run.txt","|",input_param_file="/../../file_config.json",validate=False)'`

# CHANGELOG

#release 2.3
* Updated script to use python3

#release 2.2—————————
* Modified a few threading/exception handling in hopes of improving reliability
* Added optionality for insights and householding. UPDATE YOUR CONFIG JSONS
* Refactored a few of the file writing methods

#release 2.1—————————
Implemented “pass through” columns in case you want to pass through data from the original input file. 
* Only works when you read configs from a file. 
* Enter them in the “passThroughColumns” section of the config file. 

Stats now computed on first few batches so you can see if you have any maintained links

Improved error handling of file parsing errors

Refactored to use the new “insights” bundle to get “dense” / strength

