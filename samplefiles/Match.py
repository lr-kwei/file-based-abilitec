import sys
import json
import callDSAPI
from boto.gs.lifecycle import AGE

def main(argv):
    r'Please look at our OAuth2 examples about how to obtain an access token.'
    accessToken = argv[0]
    
    callPeopleMatch(accessToken)
    callPlacesMatch(accessToken)
    callHouseholdsMatch(accessToken)
    callEntitiesMatch(accessToken)
    callBatchMatch(accessToken)
    
def callPeopleMatch(accessToken):
    r'This example does match on People document class using input of name and address.'
    endpoint = "/people/match"
    
    nameAddress = callDSAPI.getSampleRecordWithNameAddress()
    options = callDSAPI.getPeopleMatchOptions()
    payload = dict(json.loads(nameAddress).items() + json.loads(options).items())
    
    response = callDSAPI.get(endpoint, accessToken, payload)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
        responseBody = json.loads(response.text)
        person = responseBody['person']
        if 'abilitec' in person:
            print 'consumer link=' + person['abilitec']['consumerLink']
        if 'basicDemographics' in person:
            age = person['basicDemographics']['age'] if 'age' in person['basicDemographics'] else ''
            occupation = person['basicDemographics']['occupation'] if 'occupation' in person['basicDemographics'] else ''
            print 'age=' + str(age)
            print 'occupation=' + occupation 
    else:
        print 'People match call returned ' + str(statusCode)

def callPlacesMatch(accessToken):
    endpoint = "/places/match"
    
    address = callDSAPI.getSampleRecordWithAddress()
    payload = json.loads(address)
    
    response = callDSAPI.get(endpoint, accessToken, payload)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
        responseBody = json.loads(response.text)
        place = responseBody['place']
        if 'id' in place:
            print 'id=' + place['id']
    else:
        print 'Places match call returned ' + str(statusCode)
    
def callHouseholdsMatch(accessToken):
    endpoint = "/households/match"
    
    nameAddress = callDSAPI.getSampleRecordWithNameAddress()
    payload = json.loads(nameAddress)
    
    response = callDSAPI.get(endpoint, accessToken, payload)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
    else:
        print 'Households match call returned ' + str(statusCode)
    
def callEntitiesMatch(accessToken):
    endpoint = "/entities/match"
    
    nameAddress = callDSAPI.getSampleRecordWithNameAddress()
    payload = json.loads(nameAddress)
    
    response = callDSAPI.get(endpoint, accessToken, payload)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
    else:
        print 'Entities match call returned ' + str(statusCode)
    
def callBatchMatch(accessToken):
    endpoint = "/batch/match"
    
    batchRequest = callDSAPI.getBatchRequestRecords()
    payload = json.dumps(batchRequest)
    
    response = callDSAPI.post(endpoint, accessToken, payload)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
        responseBody = json.loads(response.text)
        for i in range(len(responseBody)):
            res = responseBody[i]
            if res['code'] == 200:
                document = res['document']
                if 'person' in document:
                    print 'id=' + document['person']['id']
                    print 'consumer link=' + document['person']['abilitec']['consumerLink']
                    
    else:
        print 'Batch match call returned ' + str(statusCode)
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: python Match.py accessToken"
        sys.exit(1)
    main(sys.argv[1:])