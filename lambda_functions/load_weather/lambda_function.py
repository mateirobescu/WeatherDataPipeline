import datetime
import json
from operator import itemgetter

import pymysql
import boto3
import requests
from botocore.exceptions import ClientError
from pymysql.cursors import Cursor

BUCKET = "raw-weather-data--mateirobescu"

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


def getLastS3Obj() -> str|None:
	s3_client = boto3.client('s3')
	try:
		response = s3_client.list_objects_v2(
			Bucket=BUCKET,
			Prefix="raw/"
		)
	except ClientError as e:
		print(f"Error accessing Bucket {BUCKET}: {e}")
		return None
	
	if 'Contents' not in response:
		print(f"No objects found in Bucket {BUCKET}.")
		return None
	
	latest_object = max(response['Contents'], key=itemgetter('LastModified'))
	return latest_object['Key']
	

def getS3ContentFromKey(key: str) -> dict|None:
	s3_client = boto3.client('s3')
	
	try:
		response = s3_client.get_object(
			Bucket=BUCKET,
			Key = key
		)
		file_content = response['Body'].read().decode('utf-8')
		content_json = json.loads(file_content)
		
		return content_json
		
	except s3_client.exceptions.NoSuchKey:
		print(f"Error: Object with key '{key}' not found in the Bucket: {BUCKET}'.")
		return None
	except ClientError as e:
		print(f"An error occurred while getting the object with key({key}) from Bucket({BUCKET}): {e}")
		return None
	
	
def deleteS3Object(key: str):
	s3_client = boto3.client('s3')
	
	try:
		s3_client.delete_object(Bucket=BUCKET, Key=key)
	except ClientError as e:
		print(f"Failed to delete {key} from Bucket({BUCKET}): {e}")


def addCountry(cursor: Cursor, countryCode: str) -> None:
	URL = "https://restcountries.com/v3.1/alpha"
	response = requests.get(f"{URL}/{countryCode}", timeout=10)
	
	if response.status_code != 200:
		raise Exception(f"Country API for {countryCode} could not be accessed!")
	
	data = response.json()
	if not data:
		raise ValueError(f"Invalid country code for {countryCode}!")
	data = data[0]
	
	official_name = data["name"]["official"]
	common_name = data["name"]["common"]
	iso2_code = data["cca2"]
	iso3_code = data["cca3"]
	region = data["region"]
	subregion = data["subregion"]
	
	try:
		cursor.execute(
			"""
			INSERT INTO countries
				(official_name, common_name, iso2_code, iso3_code, region, subregion)
			VALUES (%s, %s, %s, %s, %s, %s)
			""",
			(official_name, common_name, iso2_code, iso3_code, region, subregion)
		)
	except pymysql.IntegrityError:
		pass
	except pymysql.MySQLError as e:
		raise RuntimeError(f"Failed to insert country {countryCode}: {e}")


def addCity(cursor: Cursor, weatherData: dict) -> None:
	iso2_code = weatherData['sys']['country']
	
	cursor.execute("""
	SELECT id
	FROM countries
	WHERE UPPER(iso2_code) = UPPER(%s);
	""", (iso2_code,))
	
	cityId = str(weatherData['id'])
	countryId = cursor.fetchone()[0]
	name = weatherData['name']
	latitude = weatherData['coord']['lat']
	longitude = weatherData['coord']['lon']
	
	try:
		cursor.execute(
			"""
			INSERT INTO cities
				(id, country_id, name, latitude, longitude)
			VALUES (%s, %s, %s, %s, %s)
			""",
			(cityId, countryId, name, latitude, longitude)
		)
	except pymysql.IntegrityError:
		pass
	except pymysql.MySQLError as e:
		raise RuntimeError(f"Failed to insert city {name}({cityId}): {e}")


def addWeatherReading(cursor: Cursor, weatherData: dict):
	timestamp = weatherData['dt']
	date = datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC).date()
	cityId = weatherData['id']
	main = weatherData['weather'][0]['main']
	description = weatherData['weather'][0]['description']
	temperature = weatherData['main']['temp']
	feelsLike = weatherData['main']['feels_like']
	temperatureMin = weatherData['main']['temp_min']
	temperatureMax = weatherData['main']['temp_max']
	windSpeed = weatherData['wind']['speed']
	windDeg = weatherData['wind'].get('deg')
	humidity = weatherData['main']['humidity']
	pressure = weatherData['main']['pressure']
	
	try:
		cursor.execute(
			"""
            INSERT INTO weather_readings
            (date, city_id, main, description, temperature, feels_like, temperature_min,
             temperature_max, wind_speed, wind_deg, humidity, pressure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			""",
			(
				date,
				cityId,
				main,
				description,
				temperature,
				feelsLike,
				temperatureMin,
				temperatureMax,
				windSpeed,
				windDeg,
				humidity,
				pressure
			)
		)
	except pymysql.IntegrityError as e:
		pass
	except pymysql.MySQLError as e:
		raise RuntimeError(f"Failed to insert weather reading for city {cityId}: {e}")

def lambda_handler(event, context):
	credentials = getDbCreds()
	conn = connectToDB(*credentials)
	
	if 'Records' in event:
		records = event['Records'][0]
		key = records["s3"]["object"]["key"]
	else:
		key = getLastS3Obj()
		
	if key is None:
		return {"statusCode": 400, "body": "No files to process"}
	data = getS3ContentFromKey(key)
	
	try:
		with conn.cursor() as cursor:
			countryCode = data['sys']['country']
			
			addCountry(cursor, countryCode)
			addCity(cursor, data)
			addWeatherReading(cursor, data)
			
			conn.commit()
			deleteS3Object(key)
	finally:
		conn.close()
	
	return {"statusCode": 200, "body": f"Object({key}) was handled!"}