#
set -e

DB_HOST=$1
DB_PORT=$2
DB_NAME=$3
DB_USER=$4
DB_PASSWORD=$5
IMPORT_DATA=$6


if [ "$IMPORT_DATA" = true ]; then
  echo "Starting import..."

  psql -h $DB_HOST -U $DB_USER -d $DB_NAME  -f ./dump_data

  echo "Import complete."
else
  echo "Dump Data not being imported. The value of the env var 'IMPORT_DATA' is not set to true."
fi


