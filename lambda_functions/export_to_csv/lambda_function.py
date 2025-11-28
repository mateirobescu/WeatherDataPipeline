from collections import defaultdict

import boto3
from botocore.exceptions import ClientError
import json
import pymysql

BUCKET_NAME = "raw-weather-data--mateirobescu"

def getDbCreds():
	session = boto3.session.Session()
	client = session.client(
		service_name='secretsmanager',
		region_name='eu-north-1'
	)
	
	try:
		get_secret_value_response = client.get_secret_value(
			SecretId="RdsWeatherDataCredentials"
		)
	except ClientError as e:
		raise e
	
	secret = get_secret_value_response["SecretString"]
	secret_data = json.loads(secret)
	
	return secret_data["USER"], secret_data["PASSWORD"], secret_data["HOST"], secret_data["DBNAME"]

def connectToDB(user, password, host, dbname):
	return pymysql.connect(
		host=host,
		user=user,
		password=password,
		database=dbname,
		connect_timeout=10
	)


def lambda_handler(event, context):
	credentials = getDbCreds()
	conn = connectToDB(*credentials)
	table_cols = {}
	
	try:
		with conn.cursor() as cursor:
			cursor.execute("SHOW TABLES")
			tables = cursor.fetchall()
			for table in tables:
				table = table[0]
				cursor.execute(f"DESCRIBE `{table}`")
				columns = cursor.fetchall()
				table_cols[table] = set(col[0] for col in columns)
			
			if 'columns' not in event:
				return {"statusCode": 404, "body": "No columns specified!"}
			
			select_cols = []
			for column in event['columns']:
				table, col = column.split(':')
				if table not in table_cols:
					return {"statusCode": 404, "body": f"Table {table} doesn't exist!"}
				
				if col not in table_cols[table]:
					return {"statusCode": 404, "body": f"Column {col} doesn't exist!"}
				
				select_cols.append(f"`{table}`.`{col}`")
			
			select_statement = ', '.join(select_cols)
			
			cursor.execute(f"""
			SELECT {select_statement}
			FROM countries
			JOIN cities
				ON countries.id = cities.country_id
			JOIN weather_readings
				ON cities.id = weather_readings.city_id
			""")

			print(cursor.fetchall())
	
	finally:
		conn.close()
		
	
	return {"statusCode": 200, "body": "Success!"}
	