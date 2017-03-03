Mulesoft's CloudHub is a PaaS platform where the logs are visible via the Web console or
also available via CloudHub api calls.

The author of this program is NOT and CAN NOT be liable for anything this program may cause.

This is a FREE program for you to use and re-distribute!  The source code is included in case you
want to enhance.  Reading this file is required before you are allowed to use this program.
By use this program, your are in agreement with the proceeding statements.

Have fun!

#################### INPUT ###############################
This program requires the presence of the mule2sumo.json configuration file

{
  "sumo_url": "You generate this URL from Sumo Logic's hosted collector",
  "domain": "this a substring to be queried against the application list",
  "application_url": "https://anypoint.mulesoft.com/cloudhub/api/v2/applications",
  "auth": "https://anypoint.mulesoft.com/accounts/login",
  "username": "a_log_reader_account",
  "password": "the_password"
}

For example:
Assume you have your applications named abc_prd_v1, prd_xyz_b1, nbc_v1_prd, and prod_fox_ex1, if you set the "domain" as "prd",
this program will upload the logs from actively running abc_prd_v1, prd_xyz_b1,nbc_v1_prd, but NOT prod_fox_ex1 domains.

################## OUTPUT ################################
This program output THREE files:
mule2sumo.log : contains the activity log
mule2sumo.marker : contains markers for each deployment_id
mule-xxxxx-yyyyy.out : which are temp log files from Mulesoft's Cloudhub to be uploaded



------------------ Requirements --------------
Installing Python runtime

pip install requests
pip install simplejson
