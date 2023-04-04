#
set -e


echo "Starting import..."

pg_restore -h $WRITE_DB_CONNECTION_HOST -U $WRITE_DB_CONNECTION_USERNAME -d $WRITE_DB_CONNECTION_DATABASE  ./dump_data

echo "Import complete."