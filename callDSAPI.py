import requests
import json
import urllib
import hashlib

# version 1.0

DSAPI_URL = "https://us.am-staging.identity.api.liveramp.com/"

def get(uri, accessToken, payload=None):
    headers = {
        "Authorization": "Bearer " + accessToken, #This header is required
        "Accept": "application/json" #this can be application/xml or text/html
    }
    response = requests.get(DSAPI_URL+uri, params=payload, headers=headers, timeout=10)
    # response = {"person": {"id": "5a5a5a5a00d1259d57e2097710dba53c20a26e7db6","householdId": "5a5a5a5a00f3c1e266b1ed36185b4da43f0c98862e","abilitec": {"consumerLink": "003YUS02XKRLMYCQ"} } }
    # response = {"group": {"people": [{"person": {"id": "ca5a5a5a00d1259d57e2097710dba53c20a26e7ab6","householdId": "1a5a5a5a00f3c1e266b1ed36185b4da43f0c988ee1","abilitec": {"consumerLink": "003YUS02XKRLMYCQ"}}},
    #                                 {"person": {"id": "5a5a5a5a00d1259d57e2097710dba53c20a26e7b32","householdId": "5a5a5a5a00f3c1e266b1ed36185b4da43f0c98862e","abilitec": {"consumerLink": "003YUS01AFBEKFHD"}}},
    #                                 {"person": {"id": "f35a5a5a00d1259d57e2097710dba53c20a26e7ddb","householdId": "125a5a5a00f3c1e266b1ed36185b4da43f0c9886f4","abilitec": {"consumerLink": "003YUS02UAJDEOFC"}}}]
    #                      }
    #            }
    return response

def post(uri, accessToken, payload):
    headers = {
        "Authorization": "Bearer " + accessToken, #This header is required
        "Content-type": "application/json"
    }
    response = requests.post(DSAPI_URL+uri, data=payload, headers=headers, timeout=10)
    return response



#################################################################################################################################################
# The following functions are for building test records using synthetic data available in sandbox
#################################################################################################################################################
def getSampleRecordWithNameAddress():
    return '{"firstName": "CADYN", "lastName": "TIERNEY", "streetAddress": "3111 N RANKIN ST", "city": "APPLETON", "state": "WI", "zipCode": "54911"}'

def getPeopleMatchOptions():
    return '{"bundle": "abilitec,basicDemographics,causesAndVolunteer,creditAndBankCards,insurance", "limit": 1}'

def getSampleRecordWithAddress():
    return '{"primaryNumber": "5305", "preDirectional": "W", "street": "SUMMIT", "streetSuffix": "AVE", "city": "BARTONVILLE", "state": "IL", "zipCode": "61607"}'

def getSampleRecords():
    return ['{"firstName": "CADYN", "lastName": "TIERNEY", "streetAddress": "3111 N RANKIN ST", "city": "APPLETON", "state": "WI", "zipCode": "54911"}',
            '{"firstName": "ORPHA", "middleName": "FLORIDA", "lastName": "TIERNEY", "streetAddress": "5305 W SUMMIT AVE", "city": "BARTONVILLE", "state": "IL", "zipCode": "61607"}',
            '{"firstName": "ELISHEVA", "lastName": "KEEFE", "streetAddress": "5519 SEAVIEW ST", "city": "RUSTON", "state": "WA", "zipCode": "98407"}']

def getBatchRequestRecords():
    requestType = "/people/match?";
    inputRecords = getSampleRecords()
    outputRecords = []

    for record in inputRecords:
        encoded = urllib.urlencode(json.loads(record))
        outputRecords.append(requestType+encoded)

    return outputRecords

def getERWithNameAddress():
    r'This is an ER record represented by name and postal address elements'
    return 'Matthias New 215 Waukee Ave Clive IA 50263'

def getERLWithEmail():
    r'This is an ER record in SHA1 hash'

    er = 'charlesjohnson2test@acxiom.com'
    m = hashlib.sha1()   #MD5 is also supported
    m.update(er)

    return m.hexdigest()

def getERWithAbilitecLink():
    return '0000US0209B0QJ0Y'

def getERLookupOptions():
    return '{"bundle": "abilitec,basicDemographics,creditAndBankCards,insurance", "docIdOnly": false}'

def getERBatchRequest():
    requestType = "/entities/er/";
    sampleRecords = getSampleRecords();
    outputRecords = []

    for record in sampleRecords:
        jsonRecord = json.loads(record)
        firstName = jsonRecord['firstName']
        middleName = jsonRecord['middleName'] if ('middleName' in jsonRecord) else ''
        lastName = jsonRecord['lastName']
        streetAddress = jsonRecord['streetAddress']
        city = jsonRecord['city']
        state = jsonRecord['state']
        zipCode = jsonRecord['zipCode']

        er = requestType + firstName + ' ' + middleName + ' ' + lastName + ' ' + streetAddress + ' ' + city + ' ' + state + ' ' + zipCode
        er = ' '.join(er.split()).lower() #extra spaces between elements need to be removed
        outputRecords.append(er);

    return outputRecords
