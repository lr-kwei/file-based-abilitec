import sys
import json
import urllib
import callDSAPI

def main(argv):
    r'Please look at our OAuth2 examples about how to obtain an access token.'
    accessToken = argv[0]
    
    callERLookup(accessToken)
    callAbilitecLookup(accessToken)
    callSHA1Lookup(accessToken)
    callBatchLookup(accessToken)
    
def callERLookup(accessToken):
    r'This example does Entity Representation lookup on People document class using input of name and address.'
    endpoint = "/people/er/"
    
    lookupValue = callDSAPI.getERWithNameAddress()
    data = urllib.quote(lookupValue)
    uri = endpoint + data
    
    options = callDSAPI.getERLookupOptions()
    params = urllib.urlencode(json.loads(options))
    
    response = callDSAPI.get(uri, accessToken, params)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
    else:
        print 'ER lookup call returned ' + str(statusCode)

def callAbilitecLookup(accessToken):
    r'This example does Abilitec lookup on People document class using input of Consumer Link.'
    endpoint = "/people/abilitec/"
    
    lookupValue = callDSAPI.getERWithAbilitecLink();
    uri = endpoint + lookupValue
    
    response = callDSAPI.get(uri, accessToken)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
    else:
        print 'Abilitec lookup call returned ' + str(statusCode)
    
def callSHA1Lookup(accessToken):
    r'This example does ERL lookup on Households document class using input of SHA1-hashed email address.'
    endpoint = "/households/sha1/"
    
    lookupValue = callDSAPI.getERLWithEmail();
    uri = endpoint + lookupValue
    
    response = callDSAPI.get(uri, accessToken)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
    else:
        print 'ERL(SHA1) lookup call returned ' + str(statusCode)

def callBatchLookup(accessToken):
    r'This example does ER lookup on Entities document class in batch mode.'
    endpoint = "/batch/lookup"
    
    payload = json.dumps(callDSAPI.getERBatchRequest())
    
    response = callDSAPI.post(endpoint, accessToken, payload)
    statusCode = response.status_code
    if (statusCode == 200):
        print response.text
    else:
        print 'Batch lookup call returned ' + str(statusCode)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: python Lookup.py accessToken"
        sys.exit(1)
    main(sys.argv[1:])