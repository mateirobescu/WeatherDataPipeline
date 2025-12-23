import json
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
	s3_client = boto3.client('s3')
	bucket_name = "raw-weather-data--mateirobescu"
	
	city_id = event["city_id"]
	
	template_response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?id={city_id}&units=metric&appid={KEY}')
	if template_response.status_code != 200:
		return {"statusCode": 400, "body": f"OpenWeatherAPI failed for city {city_id}!"}
	template = template_response.json()

	START = 1735718400 #2025-1-1 08:00
	END = datetime.datetime.now(tz=datetime.UTC).timestamp()
	curr_time = START
	
	failures = 0
	while curr_time < END:
		failed = False
		response = requests.get(f'https://history.openweathermap.org/data/2.5/history/city?id={city_id}&type=hour&start={curr_time}&end={curr_time}&units=metric&appid={KEY}')
		if response.status_code == 200:
			data = response.json()
			data = data['list'][0]
			city_name = template["name"]
			
			
			
			file_name = f"raw/{city_id}-{city_name.replace(' ', '-').encode("ascii", "ignore").decode("ascii").lower()}_{datetime.datetime.fromtimestamp(curr_time, tz=datetime.UTC).strftime('%Y-%m-%d')}.json"
			
			for field in data:
				template[field] = data[field]
			
			try:
				s3_client.put_object(
					Bucket=bucket_name,
					Key=file_name,
					Body=json.dumps(template, indent=2),
					ContentType="application/json"
				)
			except ClientError as e:
				failed = True
				print(f"Bucket {bucket_name} failed to put weather for city {city_id} at timestamp {curr_time}!")
		else:
			failed = True
			print(f"OpenWeatherAPI History failed for city {city_id} at timestamp {curr_time}!")

		if failed:
			failures += 1
			
		curr_time += 86400
	
	return {
		'statusCode': 200,
		'body': json.dumps(f"Get History finished for city {city_id} with {failures} failures.")
	}