# Usage: pass in the DB container ID as the argument

# Set database configurations
export CT_DB_USERNAME=ct_location
export CT_DB_NAME=location


cat ./db/init-db.sql | kubectl exec -i $1 -- bash -c "psql -U $CT_DB_USERNAME -d $CT_DB_NAME"

cat ./db/udaconnect_public_location.sql | kubectl exec -i $1 -- bash -c "psql -U $CT_DB_USERNAME -d $CT_DB_NAME"
