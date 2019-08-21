# This script will execute callAbiliTechwithFile.appendFile with a queue of files
# invoke with: python2.7 -c 'from callAbiliTecwithMultipleFiles import *; appendMultipleFiles("/path/filequeue.txt", True)'

import csv
import requests
import json
import collections
import time
import callAbiliTecwithFile

# version 2.0

# global variables
options = {"limit": 1, "matchLevel": "default"}  # set configs for the file. Update with optionQuery() or updateOptions() method
accessToken = {"client_id": "f7b66f06-364d-40f3-8e63-6375eec4d488", "client_secret": None, "access_token": None, "exp_time": None}  # Access token placeholder. Updated with getToken() method

def appendMultipleFiles(filename, validate=True):
    "This method reads a file of format 'filename,config_filename' and processes each file through the DS-API using the associated config"

    # create queue to hold filenames and configs
    fileQueue = []
    fq = callAbiliTecwithFile.openFile(filename, ',')  # open file with filenames
    for row in fq:  # each row is filename, config_filename
        fileQueue.append((row[0], row[1]))  # add a tuple of (file, config) to the queue

    # run file validation
    if validate:
        for pair in fileQueue:  # each iter item / pair is a tuple of filename, config_filename
            f = open(pair[1])  # open the config file in this pair
            foo = json.load(f)  # read configs into a json dict
            dl = str(foo["fileFormat"]["dl"])  # find the delimeter in the config file
            valid_file = callAbiliTecwithFile.checkFile(pair[0], dl)  # validate the file
            if not valid_file: return  # check that file passed validation

    # start processing
    for pair in fileQueue:
        newToken =  callAbiliTecwithFile.checkToken(accessToken)
        accessToken.update(newToken)  # get secret from user and get token; secret is stored and used across files to renew token each time
        callAbiliTecwithFile.appendFile(pair[0], validate=False, input_param_file=pair[1], token=accessToken)
    return

