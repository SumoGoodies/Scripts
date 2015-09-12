' This script pulls the EPO events table, additional analysis to be done in Sumo
' Script is provided 'as is' with no warranty of any kind.  

' 1. Save the following into a file, ie: c:\sumo_epo.vbs
' 2. update the Server, Database UserID, and Pwd.  <<The SQL Server needs to run in mix-authentication mode>>
' 3. SELECT the fields to be polled from the DB view or tables.
' Configure the DATEADD matches with the run interval in Sumo Source.  The script use SQL DateAdd(datepart, num, date)
' dd = day, mi=minute, hh=hour

' Sumo FER
' To be provided, contact author.
' see how to configure the script in sumo, see https://docs.google.com/document/d/1mMCZGD6t8F9unUFSCaCIzt3wmleF-6VBKbBBc4CQsh4

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
UserId = "sa"
Pwd = "blabhal"

Set Connection = CreateObject("ADODB.Connection")
' the EPOServer is the instance name, may not needed
ConnectionString = "Driver={SQL Server};Server=" & Server & "\EPOSERVER;Database=" & Database & ";Uid=" & UserId & ";Pwd=" & Pwd
Connection.Open ConnectionString

Set Recordset = CreateObject("ADODB.Recordset")

'assumes poll every 5 minutes.
SQLQuery = "SELECT AutoID,ServerID,ReceivedUTC,DetectedUTC,ThreatCategory,ThreatEventID,ThreatSeverity,ThreatName,ThreatType,ThreatActionTaken,ThreatHandled,AnalyzerName,AnalyzerHostName,SourceProcessName,SourceURL,TargetHostName,TargetFileName FROM EPOEvents where receivedUTC > DATEADD(mi, -5, GETDATE())"

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
            RecordString = RecordString & "{" & Field.name & ":" & Field.value & "} "
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
