' This script pulls the EPO events table, additional analysis to be done in Sumo
' Script is provided 'as is' with no warranty of any kind.  

' 1. Save the following into a file, ie: c:\sumo_epo.vbs
' 2. update the Server, Database UserID, and Pwd.  or you can configure the collector to run under a service account.
' 3. SELECT the fields to be polled from the DB view or tables.
' Configure the DATEADD matches with the run interval in Sumo Source.  The script use SQL DateAdd(datepart, num, date)
' considering UTC time differences
' dd = day, mi=minute, hh=hour

' Sumo FER
' To be provided, contact author.
' see how to configure the script in sumo, see https://docs.google.com/document/d/1mMCZGD6t8F9unUFSCaCIzt3wmleF-6VBKbBBc4CQsh4
'
' In sumo collector source config, you will need to setup a multi-line boundary condition as 
'  ^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{1,2}:\d{1,2}.*
'
' 07/21/2017 NOTE: For DB running with named instance, the Server should be set to "myServerName\myInstanceName"

option explicit
Dim Connection
Dim ConnectionString
Dim SQLQuery
Dim Recordset
Dim RecordString
Dim Field
Dim Server, Database, UserId, Pwd, outFile, objFSO, objFile

Server = "WIN_SQLServer"
Database = "epo_Win_SQLServer"
' the following two lines are needed if you are using SQL Server authentication
UserId = "sa"
Pwd = "blabhal"

Set Connection = CreateObject("ADODB.Connection")
' the EPOServer is the instance name, may not needed
ConnectionString = "Driver={SQL Server};Server=" & Server & ";Database=" & Database & ";Uid=" & UserId & ";Pwd=" & Pwd

' if you are use Native Windows authentication, use the following
' ConnectionString = "Driver={SQL Server};Server=" & Server & ";Database=" & Database & ";Trusted_Connection=yes" 

Connection.Open ConnectionString

Set Recordset = CreateObject("ADODB.Recordset")

'assumes poll every 5 minutes.
SQLQuery = "SELECT AutoID,ServerID,ReceivedUTC,DetectedUTC,ThreatCategory,ThreatEventID,ThreatSeverity,ThreatName,ThreatType,ThreatActionTaken,ThreatHandled,AnalyzerName,AnalyzerHostName,SourceProcessName,SourceURL,TargetHostName,TargetFileName FROM EPOEvents where receivedUTC > DATEADD(mi, -5, GETUTCDATE())"

Set objFSO=CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.GetStandardStream(1)
Recordset.Open SQLQuery, Connection
Dim timestamp, Str, s
timestamp = Now()
do until Recordset.EOF
    RecordString = timestamp & " "
    for each Field in Recordset.Fields
        'skip binary type fields - 204, 205
        if Field.Type <> 204 and Field.Type <> 205 Then
            RecordString = RecordString & "{" & Field.name & "=" & Field.value & "} "
        End If
        next
    objFile.WriteLine RecordString
    Recordset.MoveNext
loop

Recordset.Close
Set Recordset=nothing
Connection.Close
Set Connection=nothing
objFile.Close
