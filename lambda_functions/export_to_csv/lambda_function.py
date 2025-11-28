import csv
import datetime
import io
from sys import prefix
from typing import Any

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


def parseColumns(columns: list[str], table_cols: dict) -> str:
	if len(columns) == 1 and columns[0] == "*":
		return "*"
	
	select_cols = []
	for column in columns:
		table, col = column.split(':')
		if table not in table_cols:
			return {"statusCode": 404, "body": f"Table {table} doesn't exist!"}
		
		if col not in table_cols[table]:
			return {"statusCode": 404, "body": f"Column {col} doesn't exist!"}
		
		select_cols.append(f"`{table}`.`{col}` AS `{table}.{col}`")
	
	return ','.join(select_cols)


def generateKey(s3: boto3.client, name: str) -> str:
	if not name:
		name = 'query-data'
	if '_' in name:
		name = name.split('_')[0]
	
	number = 0
	date = datetime.datetime.now(tz=datetime.UTC).date().strftime("%Y-%m-%d")
	
	paginator = s3.get_paginator("list_objects_v2")
	
	for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix='csv/'):
		for obj in page.get("Contents", []):
			curr_key = obj["Key"].split('/')[-1].split('.')[0]
			elems = curr_key.split('_')
			
			if len(elems) == 2:
				curr_name = elems[0]
				curr_number = 0
				curr_date = elems[1]
			else:
				curr_name = elems[0]
				curr_number = int(elems[1])
				curr_date = elems[2]
			
			if name != curr_name:
				continue
			
			if date != curr_date:
				continue
			
			number = max(number, curr_number + 1)
	
	if number == 0:
		return f"csv/{name}_{date}.csv"
	return f"csv/{name}_{number}_{date}.csv"



def export_to_csv(query_data: tuple[tuple[Any]], name: str) -> None:
	s3 = boto3.client('s3')
	key = generateKey(s3, name)
	
	csv_buffer = io.StringIO()
	csv_writer = csv.writer(csv_buffer)
	
	for row in query_data:
		csv_writer.writerow(row)
		
	s3.put_object(
		Bucket=BUCKET_NAME,
		Key=key,
		Body=csv_buffer.getvalue()
	)


def lambda_handler(event, context):
	credentials = getDbCreds()
	conn = connectToDB(*credentials)
	
	try:
		with conn.cursor() as cursor:
			cursor.execute("SHOW TABLES")
			tables = cursor.fetchall()
			
			table_cols = {}
			for table in tables:
				table = table[0]
				cursor.execute(f"DESCRIBE `{table}`")
				columns = cursor.fetchall()
				table_cols[table] = set(col[0] for col in columns)
			
			if 'columns' not in event:
				return {"statusCode": 404, "body": "No columns specified!"}
			
			select_statement = parseColumns(event['columns'], table_cols)
			
			cursor.execute(f"""
			SELECT {select_statement}
			FROM countries
			JOIN cities
				ON countries.id = cities.country_id
			JOIN weather_readings
				ON cities.id = weather_readings.city_id
			""")

			header = [col[0] for col in cursor.description]
			rows = cursor.fetchall()

			query_data = [header] + list(rows)
			name = ''
			if 'name' in event:
				name = event['name']
				
			export_to_csv(query_data, name)
	
	finally:
		conn.close()
		
	
	return {"statusCode": 200, "body": "Success!"}
	