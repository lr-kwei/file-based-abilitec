# invoke using this syntax: python2.7 -c 'from callAbiliTecwithFile import *; appendFile("/home/jsloan/abilitecapi/full_pii_headers_ak.txt","\t")'

import csv
import json
import collections
import callDSAPI
import filestats
import requests
import urllib.request, urllib.parse, urllib.error
import time
from threading import Thread
from queue import Queue

# version 2.3

### TO DO
# add retry for certain status codes
# recursive retry with smaller baches when a batch retries too many times
# add lookup endpoint
# more than one touch point of each type in the file?
# handle file not square errors ?
# handle blank audience key field ?
# add debugging code / verbosity functionality
# client encoding?


# global variables
endpoint = "/people/match?"  # define endpoint for API
batchEndpoint = "/batch/match"  # define endpoint for batch calls
accessToken = {"client_id": "colin-onboarding-test-client", "client_secret": "1243c4ad-5532-4492-ad38-a9a4e61a7362", "access_token": None, "exp_time": 0}  # Access token placeholder
maxBatchSize = 1000
configDict = {"endpointOptions": {"limit": 1, "matchLevel": "default"}, "outputOptions": {"insights": "y", "households": "y"}, "touchPointColumns": collections.OrderedDict(), "passThroughColumns": collections.OrderedDict(), "fileFormat": {"ak": None}}  # set configs for the filemaxBatchSize = 1000


def appendFile(fname, dl=None, validate=True, person_id='docID', input_param_file=0, token=accessToken):
    "Processes file with file name 'fname' and delimeter 'dl' through the AbiliTec API"
    if input_param_file:
        f = open(input_param_file)
        file_params = json.load(f, object_pairs_hook=collections.OrderedDict)
        configDict.update(file_params)  # load all the configs from the file into the config variable
        for param in list(configDict["touchPointColumns"].keys()):  # remove the touch point params that aren't populated
            try:
                configDict["touchPointColumns"][param] = int(configDict["touchPointColumns"][param])
            except ValueError:
                configDict["touchPointColumns"].pop(param)
        for param in list(configDict["passThroughColumns"].keys()):  # remove the pass through params that aren't populated
            try:
                configDict["passThroughColumns"][param] = int(configDict["passThroughColumns"][param])
            except ValueError:
                configDict["passThroughColumns"].pop(param)
        valid_file = True if not validate else checkFile(fname, str(configDict["fileFormat"]["dl"]))  # validate the file
        if not valid_file: return  # check that file passed validation
        of = openFile(fname, str(configDict["fileFormat"]["dl"]))  # open file reader object
        if str(configDict["fileFormat"]["header"]).lower() == 'y': head_row = next(of)  # handle header row

    else:
        configDict["personID"] = str(person_id)  # add the person ID to the config
        configDict["fileFormat"]["dl"] = str(dl)
        valid_file = True if not validate else checkFile(fname, str(configDict["fileFormat"]["dl"]))  # validate the file
        if not valid_file: return  # check that file passed validation
        of = openFile(fname, str(configDict["fileFormat"]["dl"]))  # open file reader object
        buildMapping(of)  # build mapping of touch points in file
        endpointOptionQuery()  # configure options for API calls
        configFile = createConfigFile(fname)  # write to a file here
        print(("New config file created: " + configFile))

    accessToken.update(token)  # if a token was passed in bind global variable to it
    checkToken()  # check for valid access token
    new_fname = createNewFile(fname, str(configDict["fileFormat"]["dl"]), str(configDict["personID"]))  # create file to hold responses
    failed_fname = createFailedFile(fname, str(configDict["fileFormat"]["dl"]))  # create file to hold failed batches and calls
    rows_processed = partitionAndCall(of, new_fname, failed_fname, 250000, 100, str(configDict["fileFormat"]["dl"]))  # call the method to create partitions of the file, call the API from threads, and write results to file
    print(('processing complete with ' + str(rows_processed[0]) + ' rows processed.'))
    print(('File ' + str(new_fname) + ' created with ' + str(rows_processed[2]) + ' successful rows.'))
    print(('File ' + str(failed_fname) + ' created with ' + str(rows_processed[1]) + ' failed rows.'))
    #if rows_processed[2] < 2*10**7:
     #   try:
      #      print ('\n' + 'Stats:' + '\n' + '------------------------------')
       #     filestats.computeStats(new_fname, configDict["fileFormat"]["dl"], ['ak', str(configDict["personID"])])  # compute stats on the new file
        #except Exception as e:  # gracefully catch any exception with the stats / file parsing
         #   print("Error producing stats:" + e.message)
    #else:
     #   print("The file is too large to compute stats. Use RedShift.")
    return


def createNewFile(fname, dl, person_id):
    new_fname = fname.split('.')[0] + '_appended' + '.txt'
    nf = open(new_fname, 'w')  # create new file to write results
    headers = collections.OrderedDict()
    headers.update(configDict["touchPointColumns"])
    headers.update(configDict["passThroughColumns"])
    if person_id == 'clink':
        nf.write('ak' + dl + dl.join(list(headers.keys())) + dl + 'clink')
    else:
        nf.write('ak' + dl + dl.join(list(headers.keys())) + dl + 'docID')
    if configDict["outputOptions"]["households"] == 'y':
        nf.write(dl + 'hhDoc')
    if configDict["outputOptions"]["insights"] == 'y':
        nf.write(dl + 'matchLevel' + dl + 'dense' + dl + 'atResidentialAddress' + dl + 'atUndeliverableAddress' + dl + 'isDeceased' + dl + 'isInferredDeceased' + dl + 'isInactive')
    nf.write('\n')
    nf.close()
    return new_fname


def createFailedFile(fname, dl):
    failed_fname = fname.split('.')[0] + '_failed' + '.txt'  # create file to hold failed api calls and batches
    ff = open(failed_fname, 'w')  # create new file (will overwrite!)
    headers = collections.OrderedDict()
    headers.update(configDict["touchPointColumns"])
    headers.update(configDict["passThroughColumns"])
    ff.write('ak' + dl + dl.join(list(headers.keys())) + dl + 'status' + '\n')    # write header row in failed file
    ff.close()
    return failed_fname


def createConfigFile(fname):
    config_fname = fname.split('.')[0] + '_config' + '.txt'  # create file to hold failed api calls and batches
    cf = open(config_fname, 'w')  # create new file to write configs (will overwrite!)
    cf.write(json.dumps(configDict))  # write configs to file
    cf.close()
    return config_fname


def openFile(fname, dl):
    "opens file with fname and delimiter dl and returns a reader object"
    fh = open(fname, 'r')  # open file
    reader = csv.reader(fh, delimiter=dl, quoting=csv.QUOTE_NONE)  # format reader according to given delimiter
    return reader


def checkFile(fname, dl):
    "opens file and checks that the delimiter is present and it can be parsed with csv reader"
    print("validating file...")
    fh = open(fname, 'r')  # open file
    validated = True
    row_one = fh.readline()  # skip a row
    row_two = fh.readline()  # look at 2nd row
    if dl in row_two:  # check for the delimieter
        print("delimiter found in file")
    else:
        print("delimiter not found in file")
        validated = False
    fh.close()  # close file
    file = openFile(fname, dl)  # open again
    last_row_col_count = None  # set variable to compare column lengths
    row_num = 0
    while True:
        try:
            for row in file:
                row_num += 1  # increase the row num count
                this_row_col_count = 0  # set counter for this row's column count
                for col in row:
                    this_row_col_count += 1  # advance the counter of columns
                    field = str(col)  # check that each field can be converted to a string
                    if 'hsaccount' in field.lower():  # add one off handling for weird error I get with this substring in any parameter value
                        print("This file has the substring 'hsaccount' in it and that will cause the API to timeout.  Go remove that string.")
                        validated = False
                # if last_row_col_count and last_row_col_count != this_row_col_count:
                #     print("Row " + str(row_num) + " has a different number of columns (" + str(this_row_col_count) + ") from previous row (" + str(last_row_col_count) + ").")
                #     print(row)
                # last_row_col_count = this_row_col_count
            break
        except Exception as e:  # catch any exception with the csv reader parsing
            print(("error in line " + str(file.line_num) + ": " + e.message))
            validated = False
            continue
    if validated:
        print(("File " + fname + " validated successfully!"))
    else:
        print(("File " + fname + " failed to validate...cannot process."))
    return validated


def updateEndpointOptions(newOption):
    "Update options dict with a new option; adds or overwrites"
    configDict["endpointOptions"].update(newOption)
    return


def endpointOptionQuery():
    "displays user current options and asks if s/he wants to change them"
    print("Here are the current option parameters: ")
    for key in list(configDict["endpointOptions"].keys()):  # iterate through current options and print them
        print(("    " + str(key) + ": " + str(configDict["endpointOptions"][key])))
    print("\n")
    resp = input("Would you like to update any of them? (Type the param to update it, 'y' to iterate through them all, 'n' to keep current params): ")

    if resp.lower() == "y":  # if the user wants to update, iterate through the list and query for an update
        for key in list(configDict["endpointOptions"].keys()):
            upd = input(key + ": " + str(configDict["endpointOptions"][key]) + ". Update to: ")
            if upd:
                updateEndpointOptions({key: upd})
                print(("Updated " + key + "\n"))
                break
        endpointOptionQuery()  # ask again until user stops wanting to change things

    elif resp in list(configDict["endpointOptions"].keys()):  # user wants to change a specific option
        upd = input("New value for " + str(resp) + ": ")  # ask for the new value for that option
        updateEndpointOptions({resp: upd})
        print(("Updated " + resp + "\n"))
        endpointOptionQuery()
    return


def buildMapping(reader):
    "Builds a mapping of touch point to the corresponding column in the file."

    # default list of touch points available
    param_list = collections.OrderedDict([
                                         ("firstName", "(Person's given name. john, mary, ...)"),
                                         ("middleName", "(Person's middle name or middle initial. w, william, b, beth, ...)"),
                                         ("lastName", "(Person's family name. smith, jones, ...)"),
                                         ("generationalSuffix", "(Person's generational name suffix. jr, sr, iii, iv)"),
                                         ("name", "(Person's name. Could include first, middle, last, and suffix. john smith, mary jones, ...)"),
                                         ("primaryNumber", "(Street number in a postal address. 10, 123, 3333, ...)"),
                                         ("preDirectional", "(Street pre-directional in a postal address.  n, s, e, w, ...)"),
                                         ("street", "(Street name in a postal address. main, finley, hillsdale, ...)"),
                                         ("streetSuffix", "(Street suffix in a postal address. st, dr, rd, blvd, ...)"),
                                         ("postDirectional", "(Street post-directional in a postal address.  n, s, e, w, ...)"),
                                         ("unitDesignator", "(Secondary unit designator in a postal address.  apt, ste, fl, ...)"),
                                         ("secondaryNumber", "(Secondary number / apt number in a postal address. 12A, 4... Does not include the unit designator text like Apt., #, etc.)"),
                                         ("streetAddress", "(Full street address without city,state,zip. 101 w main st s apt 12)"),
                                         ("city", "(City. downers grove, foster city, shoreview, ...)"),
                                         ("state", "(State. 2 character standard abbreviation. ca, tn, il, ar, co, ...)"),
                                         ("zipCode", "(Zip/Postal code. 5 digit or 9 digit. 12345, 60515, 72201, ...)"),
                                         ("email", "(Email address. john.smith@somedomain.com)"),
                                         ("emailMD5", "(MD5 Hashed Email address. Note: You cannot pass in both an email and an emailMD5 parameter at the same time since they represent the same thing.)"),
                                         ("phone", "(Phone number - 10 digits without delimiters)")])

    # Figure out if there's an audience key in the file
    ak = input("Enter the column index of the Audience Key, Customer ID, or Row Number (or ENTER for none): ")
    try:
        configDict["fileFormat"]["ak"] = int(ak)
    except ValueError:
        pass

    # deal with header row
    head = input("Does this file have a header row? y or n: ")
    if head.lower() == 'y':
        configDict["fileFormat"]["header"] = "y"
        head_row = next(reader)   # read the header row into a variable
        mapped_head = input("Do the headers correspond to AbiliTec API params (case insensitive)? y or n: ")
        if mapped_head.lower() == 'y':  # if the headers correspond to AbiliTec API touch point params, iterate over them and map them
            for col in head_row:
                if col.lower() in [param.lower() for param in list(param_list.keys())]:
                    configDict["touchPointColumns"][col] = int(head_row.index(col))
        else:  # skip header row and build an ordered list of touch point parameters and the columns in which they appear in the file
            autoMap(param_list)
    else:  # no header row so use all rows
        configDict["fileFormat"]["header"] = "n"
        autoMap(param_list)
    print(configDict)
    return


def autoMap(paramDict):
    "Takes in a dictionary of touch point parameters and queries the user to indicate the corresponding columns of those touch points in the file"
    print("We need to map the touch points in the file to their column numbers.")
    print("For each touch point, enter the index of the column (First column = 0) of that parameter in the file. Press ENTER to skip a touch point.")
    for param in list(paramDict.keys()):  # iterate over the parameters in the default touch point list and ask the user what column they're in
            entry = input("Column index for " + param + ": " + paramDict[param] + "? ")
            try:
                configDict["touchPointColumns"][param] = int(entry)
            except ValueError:
                pass
    return


def partitionAndCall(source_file, target_file, failed_file, partition_size, thread_count, dl):
    "Processes a file reader, partitions the file and breaks each partition into batches, creates threads to call the API with batches, and writes results to a file"
    print("processing file...")
    q = Queue(maxsize=0)  # create queue for threads
    threadCalls = []  # list to hold results
    failedCalls = []  # list to hold failed batches and calls
    row_num = 0  # keep track of what row is being proessed
    failed_rows = 0  # keep track of how many rows failed
    successful_rows = 0  # keep track of how many rows succeeded
    partition = 0  # set counter to keep track of how many rows in the partition
    batch = []  # create a list to hold the rows in a batch to be passed to the API
    batchSize = 0   # set a counter for size of the current batch that's being built
    payloadList = []  # create a list to hold the input data from the file, to be re-written to the file with the API response
    while True:
        try:
            for row in source_file:  # iterate through the file and add rows to be processed to a batch
                try:
                    batchSize += 1  # increment the batch size counter
                    row_num += 1  # increment row counter
                    partition += 1  # increment partition counter
                    row_payload = collections.OrderedDict()  # create dictionary to hold row payload
                    for key in configDict["touchPointColumns"]:  # iterate over the mapping of API params and find the value for each param from this row
                        row_payload.update({key: row[configDict["touchPointColumns"][key]]})  # Add the value of each touch point param to the row payload dictionary
                    payload = dict(list(row_payload.items()) + list(configDict["endpointOptions"].items()))  # add the touch point params and optional params to a dictionary for this row
                    encoded = urllib.parse.urlencode(payload)  # transform the payload dictionary into a URL encoded string to pass to the API for this row
                    batch.append(endpoint+encoded)  # add the url string for this row to the list for this batch
                    for key in configDict["passThroughColumns"]: #iterate over the pass through columns and find value of each column for this row
                        row_payload.update({key: row[configDict["passThroughColumns"][key]]})  # Add the value of each pass through value to the row payload dictionary
                    try:
                        ak = row[int(configDict["fileFormat"]["ak"])]
                    except ValueError:
                        ak = row_num
                    except TypeError:
                        ak = row_num
                    payloadList.append(str(ak) + dl + dl.join(list(row_payload.values())))  # add ak and row touch points, and pass through values to a list of touch point input data (such that index of URL string list corresponds to index of row number list)

                    # once batch = batch size, add to queue, reset batch params
                    if batchSize == maxBatchSize:
                        # add to queue
                        q.put((payloadList, batch))
                        batch = []
                        batchSize = 0  # reset batch Size
                        payloadList = []
                        # del payloadList[:] # empty payload list for next batch

                    if partition >= partition_size:  # upon reaching partition size, stop and process the queue
                        if batchSize > 0:
                            q.put((payloadList, batch))
                            # del batch[:] # empty batch list for next batch
                            batch = []
                            batchSize = 0  # reset batch Size
                            payloadList = []
                            # del payloadList[:]  # reset payload L
                        checkToken()
                        for i in range(min(thread_count, partition)):  # create a Thread for each row in the queue up to max
                            worker = Thread(target=callBatch, args=(q, threadCalls, failedCalls, dl))
                            worker.setDaemon(True)
                            worker.start()
                        q.join()  # wait until the threads are finished
                        writeNewFile(threadCalls, target_file)  # parse the API responses from the threads and write them to the new file
                        writeNewFile(failedCalls, failed_file)  # write failed calls to file
                        successful_rows += len(threadCalls)  # add the number of successful rows to the counter
                        failed_rows += len(failedCalls)  # add the number of failed rows to counter
                        print(("API Calls Complete through row " + str(row_num) + ". " + str(successful_rows) + " rows successful; " + str(failed_rows) + " rows failed."))
                        partition = 0  # reset for another partition
                        if row_num < 500000:
                                    try:
                                        filestats.computeStats(target_file, configDict["fileFormat"]["dl"], ['ak',str(configDict["personID"])])  # compute stats on the first bit of the file
                                    except Exception as e:  # gracefully catch any exception with the stats / file parsing
                                        print(("Error producing stats:" + e.message))
                                        continue
                        del threadCalls[:]  # reset for another partition
                        del failedCalls[:]  # reset for another partition
                        del q
                        del batch[:]
                        del payloadList[:]
                        q = Queue(maxsize=0)  # create queue for threads
                        # print(h.heap())  # troubleshooting code

                except IndexError:
                    print(("Row " + str(row_num) + " had an IndexError. Check the number of columns in that row."))
                    rowList = []
                    rowList.append(dl.join(row) + dl + "IndexError" + "\n")
                    writeNewFile(rowList, failed_file)
                    failed_rows += 1
                    del rowList[:]
                    continue  # stop processing this row and resume with the next row
            break  # break the while loop

        except csv.Error as e:
            print(("Row " + str(row_num) + " had a csv.Error: " + str(e) + ". Check for strange characters in that row."))
            failed_rows += 1
            continue  # stop processing this row and resume with the next row

    if partition > 0:  # do this all one more time to process the remaining rows in the queue
        if batchSize > 0:
            q.put((payloadList, batch))
            # del batch[:] # reset batch
            batch = []  # reset batch
            batchSize = 0  # reset batch Size
            # del payloadList[:] # reset payload list for next batch
            payloadList = []  # reset payload List
        checkToken()
        for i in range(min(thread_count, partition)):  # create a Thread for each row, max 100
            worker = Thread(target=callBatch, args=(q, threadCalls, failedCalls, dl))
            worker.setDaemon(True)
            worker.start()
        q.join()
        writeNewFile(threadCalls, target_file)  # parse the API responses from the threads and write them to the new file
        writeNewFile(failedCalls, failed_file)  # write failed calls to file
        successful_rows += len(threadCalls)  # add the number of successful rows to the counter
        failed_rows += len(failedCalls)  # add the number of failed calls to counter
        print(("API Calls Complete through row " + str(row_num) + ". " + str(successful_rows) + " rows successful; " + str(failed_rows) + " rows failed."))
    return row_num, failed_rows, successful_rows


def callBatch(q, resultList, failedList, dl):
    "gets passed a queue with a list of input rows and a batch of urls, calls API, and returns response as a response row for each returned CLINK"
    token = accessToken["access_token"]  # get the token for calling the API
    while not q.empty():
        work = q.get()  # get a list of input params and urls from the queue
        batch = work[1]  # get the batch of uris to call
        payloadList = work[0]  # get the list of input params to write back to the file
        pay = json.dumps(batch)  # format the batch to a json object
        retry = 0  # set a counter for retries
        while retry < 10:
            try:
                time.sleep(5) # sleep for 5 seconds to separate out batches
                response = callDSAPI.post(batchEndpoint, token, pay)  # call the API
            except requests.exceptions.ConnectionError as e:  # handle connection errors
                retry += 1
                if retry == 10:
                    print("Too many connection errors; skipping batch. See _failed file for details")
                    for i in range(len(payloadList)):
                        failedList.append(payloadList[i] + dl + 'ConnectionError' + '\n')
                    break
                else:
                    # print("Connection Error " + str(e) + "...retry " + str(retry))
                    time.sleep(10)  # sleep for 10 seconds
                    continue
            except requests.exceptions.ReadTimeout as e:
                retry += 1
                if retry == 10:
                    print("Too many connection errors; skipping batch. See _failed file for details")
                    for i in range(len(payloadList)):
                        failedList.append(payloadList[i] + dl + 'ConnectionError' + '\n')
                    break
                else:
                    # print("Connection Error " + str(e) + "...retry " + str(retry))
                    time.sleep(10)  # sleep for 10 seconds
                    continue
            except requests.exceptions.HTTPError as e:
                retry += 1
                if retry == 10:
                    print("Too many connection errors; skipping batch. See _failed file for details")
                    for i in range(len(payloadList)):
                        failedList.append(payloadList[i] + dl + 'ConnectionError' + '\n')
                    break
                else:
                    # print("Connection Error " + str(e) + "...retry " + str(retry))
                    time.sleep(10)  # sleep for 10 seconds
                    continue
            except requests.exceptions.ChunkedEncodingError as e:
                retry += 1
                if retry == 10:
                    print("Too many connection errors; skipping batch. See _failed file for details")
                    for i in range(len(payloadList)):
                        failedList.append(payloadList[i] + dl + 'ConnectionError' + '\n')
                    break
                else:
                    # print("Connection Error " + str(e) + "...retry " + str(retry))
                    time.sleep(10)  # sleep for 10 seconds
                    continue

            if response.status_code == 200:  # parse the response
                response_body = json.loads(response.text)
                for i in range(len(response_body)):  # the response is a batch document
                    try:
                        res = response_body[i]  # this is each document in the batch reasponse
                        if res['code'] == 200:  # each batch document also has its own status code
                            document = res['document']  # could be a group or a person document
                            people = [document] if 'person' in list(document.keys()) else document['group']['people']  # create a list of all person documents
                            for doc in people:
                                result = ""
                                if configDict["personID"] == 'clink':
                                    clink = doc['person']['abilitec']['consumerLink'] if 'abilitec' in doc['person'] else None
                                    result += payloadList[i] + dl + str(clink)
                                else:
                                    docID = doc['person']['id']
                                    result += payloadList[i] + dl + str(docID)

                                if configDict["outputOptions"]["households"] == 'y':
                                    hhDoc = doc['person']['householdId'] if 'householdId' in doc['person'] else None
                                    result += dl + str(hhDoc)

                                if configDict["outputOptions"]["insights"] == 'y':
                                    matchLevel = doc['person']['matchMetadata']['matchConfidence'] if 'matchMetadata' in doc['person'] else None
                                    isDense = doc['person']['insights']['dense'] if 'insights' in doc['person'] and 'dense' in doc['person']['insights'] else None
                                    try:
                                        atResidentialAddress = doc['person']['insights']['allAddresses']['atResidentialAddress']
                                    except KeyError:
                                        atResidentialAddress = 'False'
                                    try:
                                        atUndeliverableAddress = doc['person']['insights']['allAddresses']['atUndeliverableAddress']
                                    except KeyError:
                                        atUndeliverableAddress = 'None'
                                    try:
                                        isDeceased = doc['person']['insights']['lifeStage']['isDeceased']
                                    except KeyError:
                                        isDeceased = 'None'
                                    try:
                                        isInferredDeceased = doc['person']['insights']['lifeStage']['isInferredDeceased']
                                    except KeyError:
                                        isInferredDeceased = 'None'
                                    try:
                                        isInactive = doc['person']['insights']['trending']['isInactive']
                                    except KeyError:
                                        isInactive = 'None'
                                    result += dl + str(matchLevel) + dl + str(isDense) + dl + str(atResidentialAddress) + dl + str(atUndeliverableAddress) + dl + str(isDeceased) + dl + str(isInferredDeceased) + dl + str(isInactive)

                                resultList.append(result + '\n')
                        else:  # if this batch doc was not code 200,  write it to the failed file
                            failedList.append(payloadList[i] + dl + str(res['document']['error']['code']) + '\n')
                            # print(payloadList[i] + dl + str(res['document']['error']['code']) )
                    except Exception as e:  # handle any other exception with parsing each document
                        print(("Error: " + str(e.message) + " " + str(e.__class__.__name__) + ". See _failed file for details"))
                        failedList.append(payloadList[i] + dl + str(e.__class__.__name__) + '\n')
                        continue
            else:  # if this batch did not produce code 200 write every call in the batch it to the failed file
                print(('People match call returned ' + str(response.status_code)))
                for i in range(len(payloadList)):
                    failedList.append(payloadList[i] + dl + str(response.status_code) + '\n')
            break  # break the while loop
        q.task_done()
    return


def writeNewFile(row_responses, new_file):
    "Reads a list of lists that contain responses and writes them to file"
    with open(new_file, 'a') as output_file:
        # print("file opened")
        for row in row_responses:
            for response in row:
                output_file.write(response)
        output_file.close()
        # print("file closed")
    return


def checkToken(token=accessToken):
    "Checks whether a token exists with sufficient time before expiration. If not prompts for new token credentials"
    client_id = token["client_id"]
    client_secret = token["client_secret"]
    if token["exp_time"] > (time.time() + 180):  # check if token exists with at least 180 secs before expiration
        print(("Token valid until: " + str(time.ctime(token["exp_time"])) + ". Current time: " + str(time.ctime())))
        return accessToken
    elif client_secret:  # if not, and there is already a key stored, use it to refresh
        getToken(client_id, client_secret)  # update the global access token
        checkToken(accessToken)
    else:  # if token is about to expire and there's not already a key stored, get it from the user
        client_secret = input("Enter client_secret for client ID " + client_id + ": ")
        getToken(client_id, client_secret)  # update the global access token
        checkToken(accessToken)
        accessToken.update({"client_secret": client_secret})
    return accessToken


def getToken(client_id, client_secret):
    "Call the AbiliTec API token endpoint to get an access token. Must pass in client_id and client_sercret."
    url = "https://us.am-staging.identity.api.liveramp.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
        }
    response = requests.post(url, data=data)  # call the token endpoint
    if response.status_code == 200:
        response_body = json.loads(response.text)
        accessToken.update({"access_token": response_body["access_token"], "exp_time": (time.time() + response_body["expires_in"])})
    else:
        print('Token call returned ' + str(response.status_code))
    return
