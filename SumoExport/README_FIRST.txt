The author of this program is NOT and CAN NOT be liable for anything this program may cause.
  
This is a FREE program for you to use and re-distribute!  The source code is included in case you 
want to enhance.  Reading this file is a required before you are allowed to use this program. 
By use this program, your are in agreement with the proceeding statements.  

Have fun!  

#################### INPUT ###############################
This program takes two arguments:
First arguement is the path to the API and Credential JSON file.
{
"api" : "Sumo Search Job API Path",
"id" : "user email address OR the access id",
"key" : "user password or the access key"
}

The api URL for Sumo US1, US2, and other Clouds are different.  If you don't know, ask Sumo support.
You should use api ID/Key that you can generate under your Sumo preference.  You can easily delete
or recreate the id/keys.
DO Keep this file safe.

Secondary arguement is path to the search query itself in JSON format.
{ "query" : "_sourcecategory=stock_trader_* | parse regex \"^(?<field1>.{10})(?<field2>.{3}?)\" | concat(field1,\",\",field2) as _raw | fields -_collector,_size,_receipttime,_source ", 
  "from" : "2015-02-03T07:00:00", 
  "to" : "2015-02-03T08:00:00", 
  "timeZone" : "CST" 
}

You should test out the query within Sumo web console first.  You will need to escape the double quotes within the query.

Both input files are within the folder as examples.

################## OUTPUT ################################
This program output THREE files:
export_data.log : contains the activity log
export_data.json : contains the complete output of the query output, including all the meta fields.
export_data.raw : contains ONLY the _raw field from the export_data.json.  The _raw in Sumo is the actual message.  If you
                  want to see output in CSV, use the concat and renaming trick as shown above.



