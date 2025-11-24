import json
import pymysql
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
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
	USER = secret_data["USER"]
	PASSWORD = secret_data["PASSWORD"]
	HOST = secret_data["HOST"]
	DBNAME = secret_data["DBNAME"]
	
	conn = pymysql.connect(
		host=USER,
		user=HOST,
		password=PASSWORD,
		database=DBNAME,
		connect_timeout=10
	)
	
	try:
		with conn.cursor() as cursor:
			cursor.execute("SELECT COUNT(*) FROM cities;")
			result = cursor.fetchone()
			print(f"Number of cities: {result[0]}")
	finally:
		conn.close()
	
	return {"statusCode": 200, "body": "Query executed successfully"}
	