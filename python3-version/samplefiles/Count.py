r'''
This example demonstrates sample calls to DSAPI Audience Select (aka Count) interface.
'''

import sys
import json
import urllib.request, urllib.parse, urllib.error
import requests

global URL

def main(argv):
    r'Please look at our OAuth2 examples about how to obtain an access token.'
    accessToken = argv[0]
    
    selectByEqualityFilter(accessToken)
    selectByRegexFilter(accessToken)
    selectByRangeFilter(accessToken)

def selectByEqualityFilter(accessToken):
    r'This example counts the audience size selected by an equality filter using GET method'
    queryString = getEqualityFilterQuery()
    encodedQuery = urllib.parse.quote(queryString, '={}')
    print(encodedQuery)
    
    response = callAudienceSelectGet(accessToken, encodedQuery)
    statusCode = response.status_code
    if (statusCode == 200):
        print(response.text)
        result = json.loads(response.text)['audience']
        count = result['count'] if 'count' in result else 0
        print('Count: ' + str(count))
    else:
        print('Audience Select call returned ' + str(statusCode))
    
    
def selectByRegexFilter(accessToken):
    r'This example counts the audience size selected by a regular expression filter using POST method'
    queryString = getRegexFilterQuery()
    
    response = callAudienceSelectPost(accessToken, queryString)
    statusCode = response.status_code
    if (statusCode == 200):
        print(response.text)
        result = json.loads(response.text)['audience']
        count = result['count'] if 'count' in result else 0
        print('Count: ' + str(count))
    else:
        print('Audience Select call returned ' + str(statusCode))
    
def selectByRangeFilter(accessToken):
    r'This example counts the audience size selected by a range filter using GET method'
    queryString = getRangeFilterQuery()
    encodedQuery = urllib.parse.quote(queryString, '={}')
    print(encodedQuery)
    
    response = callAudienceSelectGet(accessToken, encodedQuery)
    statusCode = response.status_code
    if (statusCode == 200):
        print(response.text)
        result = json.loads(response.text)['audience']
        count = result['count'] if 'count' in result else 0
        print('Count: ' + str(count))
    else:
        print('Audience Select call returned ' + str(statusCode))
    
def getEqualityFilterQuery():
    return 'query={"filter":{"term":{"person.basicDemographics.gender":"Male"}}}'
    
def getRegexFilterQuery():
    return 'query={"filter":{"regexp":{"person.postalContact.state":{"value":"[A-Z]*"}}}}'
    
def getRangeFilterQuery():
    return 'query={"filter":{"range":{"person.basicDemographics.age":{"gte":10,"lte":40}}}}'

def callAudienceSelectGet(accessToken, encodedQuery):
    headers = {
        #"Authorization": "Bearer " + accessToken #This header is required
        "Authorization": "Basic QWN4aW9tSW50ZXJuYWxEU0FQSVxqaXdhbmc6ajI5TjFuZkxrZw=="
    }
    
    response = requests.get(URL, params=encodedQuery, headers=headers)
    return response
  
def callAudienceSelectPost(accessToken, query):
    headers = {
        #"Authorization": "Bearer " + accessToken, #This header is required
        "Authorization": "Basic QWN4aW9tSW50ZXJuYWxEU0FQSVxqaXdhbmc6ajI5TjFuZkxrZw==",
        "Content-type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(URL, data=query, headers=headers)
    return response
    
if __name__ == '__main__':
    #URL = "https://api.acxiom.com/v1/audiences/acxiom/count"
    URL = "http://api.acxiom.net/v1/audiences/acxiom/count"
    if len(sys.argv) != 2:
        print("Usage: python Count.py accessToken")
        sys.exit(1)
    main(sys.argv[1:])
