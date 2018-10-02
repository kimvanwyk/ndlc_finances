docker exec -it ndlcfinances_mongo_1 sh -c mongodump
docker cp ndlcfinances_mongo_1:dump .
cp -ra dump ~/Dropbox/ndlc_all/treasurer/finance_db_data
