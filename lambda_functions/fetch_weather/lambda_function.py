import json
import boto3
from botocore.exceptions import ClientError
import requests
import datetime

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
	
	if response.status_code == 200:
		data = response.json()
		city_name = data["name"]
		
		s3 = boto3.client('s3')
		bucket_name = "raw-weather-data--mateirobescu"
		
		file_name = f"raw/{city_id}-{city_name.replace(' ', '-').encode("ascii", "ignore").decode("ascii").lower()}_{datetime.datetime.now(tz=datetime.UTC).strftime('%Y-%m-%d')}.json"
		
		
		s3.put_object(
			Bucket=bucket_name,
			Key=file_name,
			Body=json.dumps(data, indent=2),
			ContentType="application/json"
		)
		
		return {
			'statusCode': 200,
			'body': json.dumps("City Found")
		}
	
	return {
		'statusCode': 404,
		'body': json.dumps('City not found')
	}
