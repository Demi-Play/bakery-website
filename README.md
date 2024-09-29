# bakery-website
 
@migrations
rm -rf migrations/versions/*
flask db init
flask db migrate -m "Initial migration"
flask db upgrade