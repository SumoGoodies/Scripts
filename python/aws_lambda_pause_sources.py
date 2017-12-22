# SUMO API Endpoint is documented at https://help.sumologic.com/APIs/General-API-Information/Sumo-Logic-Endpoints-and-Firewall-Security

from __future__ import print_function
from botocore.vendored import requests
import json, time, os

def lambda_handler(event, context):
    session = requests.Session()
    queryHeaders = {"Content-Type": "application/json", "Accept" : "application/json"}
    APIEndpoint = os.environ['SUMO_API_ENDPOINT'] + "/collectors"
    dstCollectorPattern=os.environ['COLLECTOR_NAME_PATTERN']
    dstCatPattern = os.environ['SOURCE_CATEGORY_PATTERN']
    authData=(os.environ['SUMO_ACCESS_ID'],os.environ['SUMO_ACCESS_KEY']) 
    
    cs = json.loads(session.get(APIEndpoint + '?limit=10000', headers=queryHeaders, auth=authData).text)['collectors']
    for c in cs:
        collectorID = c['id']
        collectorName = c['name']
        #print ("checking collector = " + collectorName + " and collectorID = " + str(collectorID))
        if collectorName.startswith(dstCollectorPattern) :  # add this to the list 
            # only want modify it if it's a live source
            if (c['alive']==True) :
                # should have all the possible source collectors, now look for matching sources by sourceCategory
                print ('processing alive matched collector ' + collectorName) 
                time.sleep(1)
                ss = json.loads(session.get(APIEndpoint + "/" + str(collectorID) + "/sources", headers=queryHeaders, auth=authData).text)['sources']
                for s in ss:
                    # Not going to mess with metrics sources
                    if (s['sourceType'] <> "Graphite") and (s['sourceType'] <> "SystemStats") and ('category' in s) :
                        # if you want to, you can also use endswith(dstCatPattern) below
                        if s['category'].startswith(dstCatPattern):
                            print ("destination source found :" + str(s['id']) + " - " + str(s['name']) + " - " + str(s['category']))
                            r  = session.get(APIEndpoint + "/" + str(c['id']) + "/sources/"+ str(s['id']), headers=queryHeaders, auth=authData)
                            time.sleep(1)
                            su = json.loads(r.text)
                            etag = r.headers['etag']
                            # check if there is filter
                            if (len(su['source']['filters']) > 0) :
                                print ("existing filter=" + str(su['source']['filters']))
                                # save existing filter into description field
                                su['source']['description'] = json.dumps(su['source']['filters'])
                            su['source']['filters']=[{'regexp': 'this line should never match anything', 'filterType': 'Include', 'name': 'filter out all'}]
                            headers = {"Content-Type": "application/json", "Accept" : "application/json", 'If-Match': etag}
                            print (json.dumps(su))
                            r = session.put(APIEndpoint + "/" + str(c['id']) + "/sources/"+ str(s['id']), headers=headers, auth=authData, data=json.dumps(su))
                            print (r.status_code)
