#!/bin/bash

# Wait for SQL Server to start
sleep 20

# Use environment variable for password (set via docker-compose or command line)
SA_PWD="${SA_PASSWORD:-YourStrong@Passw0rd}"

# Restore the database
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -Q "RESTORE DATABASE AdventureWorks2014 FROM DISK = '/tmp/AdventureWorks2014.bak' WITH MOVE 'AdventureWorks2014_Data' TO '/var/opt/mssql/data/AdventureWorks2014.mdf', MOVE 'AdventureWorks2014_Log' TO '/var/opt/mssql/data/AdventureWorks2014_log.ldf'"

# Clean up
# rm /tmp/AdventureWorks2014.bak
