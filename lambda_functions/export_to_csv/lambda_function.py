import csv
import datetime
import io
from typing import Any
import boto3
from botocore.exceptions import ClientError
import json
import pymysql
import os

BUCKET = "weather-data-bucket--mateirobescu"


def validate_api_key(event):
	headers = event.get('headers', {})

	incoming_key = headers.get('x-api-key') or headers.get('X-Api-Key')
	
	expected_key = os.environ.get('APP_API_KEY')
	
	if incoming_key != expected_key:
		return False
	return True

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
		columns = []
		for table in ('countries', 'cities', 'weather_readings'):
			for col in table_cols[table]:
				columns.append(f"{table}:{col}")
	
	select_cols = []
	for column in columns:
		table, col = column.split(':')
		if table not in table_cols:
			raise Exception(f"Table {table} doesn't exist!")
		
		if col not in table_cols[table]:
			raise Exception(f"Column {col} doesn't exist!")
		
		select_cols.append(f"`{table}`.`{col}` AS `{table}.{col}`")
	
	return ','.join(select_cols)


def generateKey(s3_client: boto3.client, name: str) -> str:
	if not name:
		name = 'query-data'
	if '_' in name:
		name = name.split('_')[0]
	
	number = 0
	date = datetime.datetime.now(tz=datetime.UTC).date().strftime("%Y-%m-%d")
	
	paginator = s3_client.get_paginator("list_objects_v2")
	
	for page in paginator.paginate(Bucket=BUCKET, Prefix='csv/'):
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



def export_to_csv(query_data: list[tuple[Any]], name: str) -> str | None:
	s3_client = boto3.client('s3')
	key = generateKey(s3_client, name)
	
	csv_buffer = io.StringIO()
	csv_writer = csv.writer(csv_buffer)
	
	for row in query_data:
		csv_writer.writerow(row)
	
	try:
		s3_client.put_object(
			Bucket=BUCKET,
			Key=key,
			Body=csv_buffer.getvalue()
		)
	except ClientError as e:
		raise Exception(f"Bucket {BUCKET} could not export csv: {e}")
	
	return key


def get_body(event: dict) -> dict:
	
	body_str = event.get('body')
	
	if not body_str:
		raise ValueError("Body doesn't exist!")
		
	try:
		return json.loads(body_str)

	except json.JSONDecodeError:
		raise ValueError("Invalid body!")


def generate_download_link(file_key: str) -> str:
	s3_client = boto3.client('s3')
	
	try:
		download_url = s3_client.generate_presigned_url(
			ClientMethod='get_object',
			Params={
				'Bucket': BUCKET,
				'Key': file_key
			},
			ExpiresIn=60
		)
		
		return download_url
	except Exception as e:
		raise Exception("The download link could not be generated!")


def lambda_handler(event, context):
	if not validate_api_key(event):
		return {"statusCode": 403, "body": "Invalid API key!"}
	
	credentials = getDbCreds()
	conn = connectToDB(*credentials)
	try:
		body = get_body(event)
	except ValueError as e:
		return {"statusCode": 404, "body": e}
	
	try:
		with conn.cursor() as cursor:
			cursor.execute("SHOW TABLES")
			tables = cursor.fetchall()
			
			table_cols = {}
			for table in tables:
				table = table[0]
				cursor.execute(f"DESCRIBE `{table}`")
				columns = cursor.fetchall()
				table_cols[table] = [col[0] for col in columns]
			
			if 'columns' not in body:
				return {"statusCode": 404, "body": "No columns specified!"}
			
			try:
				select_statement = parseColumns(body['columns'], table_cols)
			except Exception as e:
				return {"statusCode": 400, "body": f"{e}"}
			
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
			if 'name' in body:
				name = body['name']
				
			try:
				file_key = export_to_csv(query_data, name)
			except Exception as e:
				return {"statusCode": 400, "body": f"{e}"}
			
			try:
				download_link = generate_download_link(file_key)
			except Exception as e:
				return {"statusCode": 400, "body": f"{e}"}
	
	finally:
		conn.close()
	
	return {
		"statusCode": 200,
		"body": json.dumps({
			"message": "Export to csv was a success!",
			"download_link": download_link,
		}
	)}
	