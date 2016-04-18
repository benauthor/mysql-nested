db:
	mysql -e "DROP DATABASE IF EXISTS nested_tmp;"
	mysql -e "CREATE DATABASE nested_tmp;"
	mysql -D nested_tmp < nested.sql
