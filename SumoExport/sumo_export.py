#!/usr/bin/env python

import requests, json, sys, time, re, os
from time import gmtime, strftime
os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.getcwd(), "cacert.pem")

# Export Logfile
logFilePath = "export_data.log"

# Where to save JSON data
jsonOutputFilePath = "export_data.json"

# Where to save RAW data
rawOutputFilePath = "export_data.raw"

# For results paging
resultsPerPage = 2500

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
    try:
        jsonFile = open(jsonFileName)
    except IOError as ex:
        sys.exit()
    jsonData = json.load(jsonFile)
    jsonFile.close()
    return jsonData

# Start logging
try:
    logFile = open(logFilePath, "a", 0)
except IOError as ex:
    # Don't proceed if we can't log
    print "Unable to open log file (" + logFilePath + "):  " + str(ex) + "\n"
    sys.exit(1)
	
# Check inputs.. arg 1 is API/cred and arg 2 is the query
argsNum = len(sys.argv)
# We want a single argument--the path to our alert data file
if argsNum != 3:
    print "Need to run this program with api_cred and query json files\nFor example: sumo_export.exe api_cred.json sumo_query.json"
    exitError(logFile, "Incorrect number of arguments received.  Exiting...", 1)

apiCredFile = sys.argv[1]
queryJSONFile = sys.argv[2]

# Read input configs
apiData = getJsonData(apiCredFile)
postData = getJsonData(queryJSONFile)

# Create our output file
try:
    jsonOutputFile = open(jsonOutputFilePath, "w", 0)
except IOError as ex:
    print "Unable to open output file (" + jsonOutputFilePath + "):  " + str(ex) + "\n"
    sys.exit(1)

logMsg(logFile, "Started data export logging.")


# We need cookies to maintain the session
session = requests.Session()

# Need to tell the web server we're sending JSON
queryHeaders = {"Content-Type": "application/json", "Accept" : "application/json"}

# Our starting point
searchJobEndpoint = str(apiData["api"])
# Credentials
authData=(str(apiData["id"]), str(apiData["key"]))

logMsg(logFile, "Executing Search")

# STEP 1:  POST to create the job
requestOut = session.post(searchJobEndpoint, headers=queryHeaders, auth=authData, data=json.dumps(postData))

# Check to make sure it was created successfully
if requestOut.status_code < 200 or requestOut.status_code > 299:
    logMsg(logFile, "Failed to create search job:  " + str(requestOut.status_code))
    sys.exit(1)

# Extract the JSON
jsonResponse = requestOut.json()

# Get our new Job ID
jobId = jsonResponse["id"]

logMsg(logFile, "Got job ID:  " + str(jobId))

# STEP 2:  Wait for it to finish executing
while True:
    requestOut = session.get(searchJobEndpoint + "/" + str(jobId), headers=queryHeaders, auth=authData)

    if requestOut.status_code < 200 or requestOut.status_code > 299:
        logMsg(logFile, "Failed to check job status:  " + str(requestOut.status_code))
    else:
        jsonResponse = requestOut.json()

        jobStatus = jsonResponse["state"]
        messageCount = jsonResponse["messageCount"]
        recordCount = jsonResponse["recordCount"]

        logMsg(logFile, "State:  " + jobStatus + \
            " -- messageCount:  " + str(messageCount) \
            + " -- recordCount:  " + str(recordCount))

        if jobStatus == "DONE GATHERING RESULTS":
            break

    time.sleep(5)

print "Message Count:  " + str(messageCount)

# STEP 3:  Get the results
currentOffset = 0

# Iterate through all results
while currentOffset < messageCount:

    # Need to calculate a proper offset if we're within (resultsPerPage) records of the end
    if (messageCount - currentOffset) < resultsPerPage:
        currentLimit = (messageCount - currentOffset)
    else:
        currentLimit = resultsPerPage

    resultsParams = {"offset" : currentOffset, "limit" : currentLimit}

    logMsg(logFile, "Gathering " + str(currentLimit) + " results")

    # Request the data
    requestOut = session.get(searchJobEndpoint + "/" + str(jobId) + "/messages", \
        headers=queryHeaders, \
        auth=authData, \
        params=resultsParams)

    if requestOut.status_code < 200 or requestOut.status_code > 299:
        logMsg(logFile, "Failed to retrieve " + str(currentLimit) + \
            " results at offset " + str(currentOffset))
        sys.exit(1)
    else:
        logMsg(logFile, "Successfully retrieved " + str(currentLimit) + \
            " results at offset " + str(currentOffset))

    jsonResponse = requestOut.json()

    # Output it
    jsonOutputFile.write(requestOut.text.encode('ascii', 'ignore') + "\n")

    # Increment and continue
    currentOffset += resultsPerPage


logMsg(logFile, "Done gathering results")


# STEP 4:  Delete the job
requestOut = session.delete(searchJobEndpoint + "/" + \
    str(jobId), headers=queryHeaders, auth=authData)

responseCode = requestOut.status_code

if requestOut.status_code < 200 or requestOut.status_code > 299:
    logMsg(logFile, "Failed to delete jobId:  " + str(jobId))
    sys.exit(1)
else:
    logMsg(logFile, "Successfully deleted jobId:  " + str(jobId))

jsonOutputFile.close()


# STEP 5:  Extract the raw message data
logMsg(logFile, "Opening JSON File:  " + jsonOutputFilePath)

# Open the JSON file
try:
    jsonInputFile = open(jsonOutputFilePath)
except IOError as ex:
    exitError(logFile, "Error opening jsonFile:  " + str(ex), 1)


try:
    rawOutputFile = open(rawOutputFilePath, "w", 0)
except IOError as ex:
    # Don't proceed if we can't write raw data
    exitError(logFile, "Unable to open output file (" + rawOutputFilePath + "):  " + str(ex) + "\n", 255)


for inputLine in jsonInputFile:

    # Load the JSON data
    jsonData = json.loads(inputLine)

    # Extract Raw Message field
    try:
        rawMessageAry = jsonData['messages']

        for mapDict in rawMessageAry:
            rawMessage = mapDict['map']['_raw']
            rawOutputFile.write(str(rawMessage) + "\n")
            #print str(rawMessage)

    except Exception as ex:
        logMsg(logFile, "Error while trying to read Raw Message from JSON:  " + str(ex))
        exitError(logFile, "Couldn't read Raw Message from JSON", 1)


# We've written all messages
rawOutputFile.close()

# And we're done with the raw file now
jsonInputFile.close()

# We're done
logMsg(logFile, "Done" + "\n")

logFile.close()

sys.exit(0)
