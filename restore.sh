cp -ra ~/Dropbox/ndlc_all/treasurer/finance_db_data dump
docker cp dump ndlcfinances_mongo_1:dump
docker exec -it ndlcfinances_mongo_1 sh -c mongorestore
