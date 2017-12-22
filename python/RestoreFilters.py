import requests, json, time

# We need cookies to maintain the session
session = requests.Session()

queryHeaders = {"Content-Type": "application/json", "Accept" : "application/json"}
APIEndpoint = 'https://api.us2.sumologic.com/api/v1/collectors'
dstCollectorPattern="your_pattern"
dstCatPattern = "your_pattern"
authData=("YOUR_ID","YOUR_KEY") 

cs = json.loads(session.get(APIEndpoint + '?limit=10000', headers=queryHeaders, auth=authData).text)['collectors']
for c in cs:
    collectorID = c['id']
    collectorName = c['name']
    #print ("checking collector = " + collectorName + " and collectorID = " + str(collectorID))
    if collectorName.startswith(dstCollectorPattern) :  # add this to the list 
        # only want to use it if it's dead already
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
                        #print su
                        # check if there is filter
                        if ('description' in su['source']) :
                            filters = json.loads(str(su['source']['description']))
                            print (filters)
                            # save existing filter into description field
                            su['source']['filters'] = filters
                        else:
                            su['source']['filters']=[]
                        headers = {"Content-Type": "application/json", "Accept" : "application/json", 'If-Match': etag}
                        print (json.dumps(su))
                        r = session.put(APIEndpoint + "/" + str(c['id']) + "/sources/"+ str(s['id']), headers=headers, auth=authData, data=json.dumps(su))
                        print (r.status_code)
