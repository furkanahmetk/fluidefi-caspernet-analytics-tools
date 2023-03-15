#
set -e


if [ "$IMPORT_DATA" = true ]; then
  echo "Starting import..."

  psql -h $WRITE_DB_CONNECTION_HOST -U $WRITE_DB_CONNECTION_USERNAME -d $WRITE_DB_CONNECTION_DATABASE   -f ./dump_data

  echo "Import complete."
else
  echo "Dump Data not being imported. The value of the env var 'IMPORT_DATA' is not set to true."
fi


