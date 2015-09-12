' This script pulls the EPO events table, additional analysis to be done in Sumo
' Script is provided 'as is' with no warranty of any kind.

' Save the following into a file, ie: c:\sumo_scom.vbs
' update the Server, Database UserID, and Pwd.  <<The SQL Server needs to run in mix-authentication mode>>
' SELECT the fields to be polled from the DB view or tables.
' Configure the DATEADD matches with the run interval in Sumo Source.
' see how to configure this in sumo: https://docs.google.com/document/d/1mMCZGD6t8F9unUFSCaCIzt3wmleF-6VBKbBBc4CQsh4
' ---------

option explicit
Dim Connection
Dim ConnectionString
Dim SQLQuery
Dim Recordset
Dim RecordString
Dim Field
Dim Server, Database, UserId, Pwd, outFile, objFSO, objFile

Server = "YOUR_DB_SERVERNAME"
Database = "OperationsManager"
UserId = "DB_READER"
Pwd = "DB_READER_PASSWORD"

Set Connection = CreateObject("ADODB.Connection")
ConnectionString = "Driver={SQL Server};Server=" & Server & ";Database=" & Database & ";Uid=" & UserId & ";Pwd=" & Pwd
Connection.Open ConnectionString

Set Recordset = CreateObject("ADODB.Recordset")
SQLQuery = "SELECT fullName,InstanceName,b.ObjectName,CounterName,LastSampledValue, b.LastModified FROM ManagedEntityGenericView as a join PerformanceCounterView as b on a.id = b.ManagedEntityId where b.LastModified > DATEADD(mi, -1, GETDATE())"

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
