#!/usr/bin/env python

import requests, json, sys, time, re, os
from time import gmtime, strftime

# Input and Logfile
logFilePath = "mule2sumo.log"
inputFile = "mule2sumo.json"
markerFile = "mule2sumo.marker"

#initialized some common used variables
domainNames = []
markerData = []
domainList = []
lastRecord = ""

# Generate a UTC timestamp
def getTimeStamp():
    timeStamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    timeStamp += "Z"
    return timeStamp

# Writes a given log message with timestamp
def logMsg(logFile, logMessage):
    timeStamp = getTimeStamp()
    logFile.write(timeStamp + ":  " + logMessage + "\n")

# Exits the script with the given error code, logging the error
def exitError(logFile, errorMsg, errorCode):
    timeStamp = getTimeStamp()
    logMsg(logFile, errorMsg)
    logMsg(logFile, "Exiting with error\n")
    logFile.close()
    sys.exit(errorCode)

# Get the JSON
def getJsonData(jsonFileName):
    jsonData={}
    try:
        jsonFile = open(jsonFileName)
        jsonData = json.load(jsonFile)
        jsonFile.close()
    except IOError as ex:
        jsonData = {}
    except ValueError as ve:
        # first time reading or the file is corrupted, treat it as brand new
        jsonData = {}
    return jsonData

# Start logging
try:
    logFile = open(logFilePath, "a")
except IOError as ex:
    # Don't proceed if we can't log
    sys.exit(1)

# Clean up old logs from previous sessions
# Open the JSON file
dirs = os.listdir(".")
for muleFile in dirs:
    if muleFile.startswith("mule-") :
        os.remove(muleFile)
    else :
        continue

# Read input configs
apiData = getJsonData(inputFile)
markerData = getJsonData(markerFile)

# We need cookies to maintain the session
session = requests.Session()

# Need to tell the web server we're sending JSON
queryHeaders = {"Content-Type": "application/json"}
authURL = str(apiData["auth"])
# Credentials
credData={"username":str(apiData["username"]),"password":str(apiData["password"])}

logMsg(logFile, "Executing Authorization")
# STEP 1:  POST to get the Authorization
requestOut = session.post(authURL, headers=queryHeaders, json=credData)

# Check to make sure it was authenicated successfully
if requestOut.status_code < 200 or requestOut.status_code > 299:
    logMsg(logFile, "Failed to authenticate:  " + str(requestOut.status_code))
    sys.exit(1)

logMsg(logFile,"Received Authorization")
# Extract the JSON
jsonResponse = requestOut.json()

# Got our access Token
accessToken = jsonResponse["access_token"]
tokenType = jsonResponse["token_type"]
queryHeaders={"Content-Type": "application/json","Authorization":str(tokenType)+" "+str(accessToken)}
applicationURL=str(apiData["application_url"])

# STEP 2: Find the list of matching Domain (or applications) that are in started state
domainName = str(apiData["domain"])
requestOut = session.get(applicationURL, headers=queryHeaders)
# Check to make sure it was authenicated successfully
if requestOut.status_code < 200 or requestOut.status_code > 299:
    logMsg(logFile, "Failed to get domain list:  " + str(requestOut.status_code))
    sys.exit(1)

jsonResponse = requestOut.json()

for domain in jsonResponse :
    if (domainName in domain["domain"] and domain["status"].startswith("STARTED")) :
        domainNames.append(domain["domain"])

# STEP 3: for each active domain, we'll find the active deploymentID
for domain in domainNames :
    requestOut = session.get(applicationURL+"/"+str(domain) + "/deployments?orderByDate=DESC", headers=queryHeaders)
    # Check to make sure it was authenicated successfully
    if requestOut.status_code < 200 or requestOut.status_code > 299:
        logMsg(logFile, "Failed to request deployments:  " + str(requestOut.status_code))
        sys.exit(1)

    jsonResponse = requestOut.json()
    deploymentID=""
    done=False
    for deployment in jsonResponse["data"] :
        if done:
            break
        deploymentID=str(deployment["deploymentId"])
        for instance in deployment["instances"] :
            if (instance["status"].startswith("STARTED")) :
                done=True
                break
    domainList.append({"domain":domain,"deployment_id":deploymentID})

# STEP 4: Load the marker file, Go through each domain with active deployments and download the latest logs
for domain in domainList :
    currentDomain = domain["domain"]
    currentDeploymentID = domain["deployment_id"]
    logMsg(logFile, "domain=" + currentDomain + " deployment_id=" + currentDeploymentID)
    # check if we have a marker for the domain/deployment_id. If not, start from scratch
    if currentDeploymentID in markerData.keys() :
        logMsg(logFile, "found deployment_id in marker file =" + currentDeploymentID)
        lastRecord = markerData[currentDeploymentID]
    else :
        lastRecord = "0"

    # Create our output file
    try:
        jsonOutputFile = open("mule-"+currentDomain+"-"+currentDeploymentID+".out", "w")
    except IOError as ex:
        logMsg(logFile,"Unabled to save mule output for domain=" + currentDomain + " with error: " + str(ex))
        sys.exit(1)

    # Calling Mule
    while True:
        payLoad = {"deploymentId": currentDeploymentID,"lowerId": lastRecord,"limit": 100}
        requestOut = session.post(applicationURL + "/" + currentDomain + "/logs", headers=queryHeaders, json=payLoad)

        if requestOut.status_code < 200 or requestOut.status_code > 299:
            logMsg(logFile, "Failed to query logs:  " + str(requestOut.status_code))
            break
        else:
            logMsg(logFile, "Successfully retrieved a batch of logs for domain = " + currentDomain)

        jsonResponse = requestOut.json()
        # Output it, if there are logs, else break loop
        if (len(jsonResponse) == 0) :
            break
        else:
            # Loop through, write to local file one record at a time
            for record in jsonResponse :
                jsonOutputFile.write(json.dumps(record)+ "\n")
                lastRecord = str(record["recordId"])
        logMsg(logFile,"last record=" + lastRecord)
    jsonOutputFile.close()
    logMsg(logFile, "Done processing domain = " + currentDomain)


# STEP 5:  Upload the logs into Sumo
sumoURL = str(apiData["sumo_url"])
queryHeaders = {"Content-Type": "application/json","X-Sumo-Name":"","X-Sumo-Host":""}

# Open the JSON file
dirs = os.listdir(".")
for muleFile in dirs:
    if muleFile.startswith("mule-") :
        d1 = muleFile.find("-")+1
        d2 = muleFile.rfind("-")
        d3 = muleFile.find(".out")
        currentDomain = muleFile[d1:d2]
        currentDeploymentID = muleFile[d2+1:d3]
    else :
        continue

    queryHeaders["X-Sumo-Name"] = currentDomain
    queryHeaders["X-Sumo-Host"] = currentDeploymentID

    try:
        jsonInputFile = open(muleFile)
    except IOError as ex:
        exitError(logFile, "Error opening jsonFile:  " + str(ex), 1)
        sys.exit(1)

    jsonData = ""
    for inputLine in jsonInputFile:
        # Load the JSON data
        jsonData = json.loads(inputLine)

        requestOut = session.post(sumoURL, headers=queryHeaders, json=jsonData)
        if requestOut.status_code < 200 or requestOut.status_code > 299:
            logMsg(logFile, "Failed to upload:  " + str(requestOut.status_code))
            break
        else:
            #update the last uploaded recordId
            markerData[currentDeploymentID]=jsonData["recordId"]

    # close the current file
    jsonInputFile.close()

# Save the marker file
try:
    with open(markerFile, 'w') as outfile:
        json.dump(markerData, outfile)
    outfile.close()
except IOError as ex:
    # Don't proceed if we can't write raw data
    exitError(logFile, "Unable to save marker file (" + markerFile + "):  " + str(ex) + "\n", 255)

# We're done
logMsg(logFile, "Done" + "\n")
logFile.close()
sys.exit(0)
