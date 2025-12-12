#!/bin/bash
set -e

# Start SQL Server in the background
/opt/mssql/bin/sqlservr &

# Wait for SQL Server to start
echo "Waiting for SQL Server to start..."
sleep 30

# Check if SQL Server is ready
for i in {1..60}; do
    if /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD:-YourStrong@Passw0rd}" -Q "SELECT 1" &>/dev/null; then
        echo "SQL Server is ready!"
        break
    fi
    echo "Waiting for SQL Server... ($i/60)"
    sleep 2
done

# Check if AdventureWorks database already exists
DB_EXISTS=$(/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD:-YourStrong@Passw0rd}" -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name = 'AdventureWorks2014'" -h -1 | tr -d ' ')

if [ "$DB_EXISTS" -eq "0" ]; then
    echo "Restoring AdventureWorks2014 database..."

    # Download backup if not present
    if [ ! -f /tmp/AdventureWorks2014.bak ]; then
        echo "Downloading AdventureWorks2014 backup..."
        curl -L -o /tmp/AdventureWorks2014.bak \
            https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks2014.bak
    fi

    # Restore the database
    /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD:-YourStrong@Passw0rd}" -Q "
        RESTORE DATABASE AdventureWorks2014
        FROM DISK = '/tmp/AdventureWorks2014.bak'
        WITH MOVE 'AdventureWorks2014_Data' TO '/var/opt/mssql/data/AdventureWorks2014_Data.mdf',
             MOVE 'AdventureWorks2014_Log' TO '/var/opt/mssql/data/AdventureWorks2014_Log.ldf',
             REPLACE
    "

    echo "AdventureWorks2014 database restored successfully!"
else
    echo "AdventureWorks2014 database already exists, skipping restore."
fi

# Create DBT user if not exists
echo "Creating DBT user..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD:-YourStrong@Passw0rd}" -Q "
    IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'imrandbtnew')
    BEGIN
        CREATE LOGIN imrandbtnew WITH PASSWORD = 'Imran@12345';
    END

    USE AdventureWorks2014;

    IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'imrandbtnew')
    BEGIN
        CREATE USER imrandbtnew FOR LOGIN imrandbtnew;
        ALTER ROLE db_owner ADD MEMBER imrandbtnew;
    END
"
echo "DBT user created successfully!"

# Keep container running by waiting for SQL Server process
wait
