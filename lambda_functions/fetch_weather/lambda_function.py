import json
import unicodedata
import requests
import datetime
import boto3
from botocore.exceptions import ClientError

def get_api_secret(secret_name, region_name):
	session = boto3.session.Session()
	client = session.client(
		service_name='secretsmanager',
		region_name=region_name
	)
	
	try:
		get_secret_value_response = client.get_secret_value(
			SecretId=secret_name
		)
	except ClientError as e:
		raise e
	
	secret = get_secret_value_response['SecretString']
	secret_data = json.loads(secret)
	return secret_data.get('API')


def lambda_handler(event, context):
	secret_name = "OpenWeatherApi"
	region_name = "eu-north-1"
	KEY = get_api_secret(secret_name, region_name)
	
	city_id = event["city_id"]
	response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?id={city_id}&units=metric&appid={KEY}')
	
	if response.status_code != 200:
		return {
			'statusCode': 404,
			'body': json.dumps(f"City with id {city_id} not found!")
		}
	
	data = response.json()
	city_name = data["name"]
	
	s3_client = boto3.client('s3')
	BUCKET = "weather-data-bucket--mateirobescu"
	
	normalized_text = unicodedata.normalize("NFKD", city_name.lower().replace(' ', '-'))
	ascii_city_name = normalized_text.encode("ascii", "ignore").decode("ascii")
	if not ascii_city_name:
		ascii_city_name = "unknown"
	
	key = f"raw/{city_id}-{ascii_city_name}_{datetime.datetime.now(tz=datetime.UTC).strftime('%Y-%m-%d')}.json"
	
	try:
		s3_client.put_object(
			Bucket=BUCKET,
			Key=key,
			Body=json.dumps(data, indent=2),
			ContentType="application/json"
		)
	except ClientError as e:
		return {
			'statusCode': 400,
			'body': f"Error putting object with key({key}) in bucket({BUCKET}): {e}"
		}
	
	return {
		'statusCode': 200,
		'body': json.dumps(f"City {city_id}-{city_name} found!")
	}
	
	