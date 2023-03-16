#
set -e



echo "Starting import..."

psql -h $WRITE_DB_CONNECTION_HOST -U $WRITE_DB_CONNECTION_USERNAME -d $WRITE_DB_CONNECTION_DATABASE -f ./dump_data.sql

echo "Import complete."



