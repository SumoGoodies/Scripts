# Free code with no warranty implified. Use it at your own risk
from copy import copy
import requests, json, sys, time, re, os, pprint
import csv
# We need cookies to maintain the session
session = requests.Session()

queryHeaders = {"Content-Type": "application/json", "Accept" : "application/json"}
# You will need to update the following API Endpoint if you are in us2, eu, or apac
APIEndpoint = 'https://api.sumologic.com/api/v1/collectors' 
# use your own Sumo API cred below
authData=("your_ID","your_KEY") 

# STEP 1:  POST to create the job
cs = json.loads(session.get(APIEndpoint + '?limit=10000', headers=queryHeaders, auth=authData).text)['collectors']

test = ['141135421','100092774'] #the collector ids of interest
for c in cs:
    collectorID = c['id']
    collectorName = c['name']
    #print ("checking collector = " + collectorName + " and collectorID = " + str(collectorID))
    if str(collectorID) in test:  # this matches that you will only update the interested collectors, not all 
        print ('processing matched ' + collectorName)
        # check if the collector is managed by the WEB/UI or JSON config
        if ('sourceSyncMode' in c) and (c['sourceSyncMode'].startswith("Json")) :
            print ("collector is managed by JSON file")
            # update the syncMode so we can manage it via API
            r  = session.get(APIEndpoint +"/"+ str(collectorID), headers=queryHeaders, auth=authData)
            time.sleep(1)
            su = json.loads(r.text)
            etag = r.headers['etag']
            su['collector']['sourceSyncMode'] = "UI"
            headers = {"Content-Type": "application/json", "Accept" : "application/json", 'If-Match': etag}
            r = session.put(APIEndpoint + "/"+ str(collectorID), headers=headers, auth=authData, data=json.dumps(su))
            # if success, update the sources, else move on
            if r.status_code == requests.codes.ok:
                print (r.text)
            else :
                continue             
        
        curSourcesEndpoint = APIEndpoint + "/" + str(collectorID) + '/sources'
        sourceJSON = json.loads(session.get(curSourcesEndpoint, headers=queryHeaders, auth=authData).text)['sources']
        for source in sourceJSON:
            sid = source['id']
            catg = source['category']
            if catg.startswith("app_env") :  # this is the ones that I want to update, you can use other conditions
                print ("matched category = " + catg)
                # udate this category
                # query for source again for the etag
                r  = session.get(curSourcesEndpoint +"/"+ str(sid), headers=queryHeaders, auth=authData)
                time.sleep(1)
                su = json.loads(r.text)
                etag = r.headers['etag']
                su['source']['category'] = "prod_env"+catg[7:] # this is what I wanted the new category to be, you use your own logic
                headers = {"Content-Type": "application/json", "Accept" : "application/json", 'If-Match': etag}
                print (json.dumps(su))
                # the next line is where the UPDATE happens.. the whole JSON with modifiable fields must present for updates.
                # uncomment the next line for testing.. the above line should print out the exacts to be updated.
                r = session.put(curSourcesEndpoint + "/"+ str(sid), headers=headers, auth=authData, data=json.dumps(su))
                if r.status_code == requests.codes.ok:
                    print (r.text)
                else :
                    continue                
