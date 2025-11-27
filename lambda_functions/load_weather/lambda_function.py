import datetime
import json
from operator import itemgetter

import pymysql
import boto3
import requests
from botocore.exceptions import ClientError
from pymysql.cursors import Cursor

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

def getLastS3Obj() -> str|None:
	s3 = boto3.client('s3')
	try:
		response = s3.list_objects_v2(
			Bucket=BUCKET_NAME,
			Prefix="raw/"
		)
	except Exception as e:
		print(f"Error accessing S3 bucket: {e}")
		return None
	
	if 'Contents' not in response:
		print(f"No objects found in bucket.")
		return None
	
	latest_object = max(response['Contents'], key=itemgetter('LastModified'))
	return latest_object['Key']
	

def getS3ContentFromKey(key: str) -> dict|None:
	s3 = boto3.client('s3')
	
	try:
		response = s3.get_object(
			Bucket=BUCKET_NAME,
			Key = key
		
		)
		file_content = response['Body'].read().decode('utf-8')
		content_json = json.loads(file_content)
		
		return content_json
		
	except s3.exceptions.NoSuchKey:
		print(f"Error: Object with key '{key}' not found in the bucket'.")
		return None
	except Exception as e:
		print(f"An error occurred while getting the object: {e}")
		return None
	
	
def deleteS3Object(key: str):
	s3 = boto3.client('s3')
	
	try:
		s3.delete_object(Bucket=BUCKET_NAME, Key=key)
	except Exception as e:
		print(f"Failed to delete {key}: {e}")


def addCountry(cursor: Cursor, countryCode: str) -> None:
	URL = "https://restcountries.com/v3.1/alpha"
	response = requests.get(f"{URL}/{countryCode}", timeout=10)
	
	if response.status_code != 200:
		raise Exception("Country API could not be accessed!")
	
	data = response.json()
	if not data:
		raise ValueError("Invalid country code!")
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


def addCity(cursor: Cursor, weatherData: dict) -> bool:
	iso2_code = weatherData['sys']['country']
	
	cursor.execute("""
	SELECT id
	FROM countries
	WHERE UPPER(iso2_code) = UPPER(%s);
	""", (iso2_code, ))
	
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


def addWeatherReading(cursor: Cursor, data: dict):
	timestamp = data['dt']
	date = datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC).date()
	cityId = data['id']
	main = data['weather'][0]['main']
	description = data['weather'][0]['description']
	temperature = data['main']['temp']
	feelsLike = data['main']['feels_like']
	temperatureMin = data['main']['temp_min']
	temperatureMax = data['main']['temp_max']
	windSpeed = data['wind']['speed']
	windDeg = data['wind'].get('deg')
	humidity = data['main']['humidity']
	pressure = data['main']['pressure']
	
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
	
	key = getLastS3Obj()
	if key is None:
		print("No raw weather objects found.")
		return {"statusCode": 200, "body": "No files to process"}
	
	data = getS3ContentFromKey(key)
	
	try:
		with conn.cursor() as cursor:
			countryCode = data['sys']['country']
			
			addCountry(cursor, countryCode)
			addCity(cursor, data)
			addWeatherReading(cursor, data)
			
			cursor.execute("""
			SELECT *
			FROM countries co
			JOIN cities ci
				ON co.id = ci.country_id
			JOIN weather_readings wr
				ON ci.id = wr.city_id
			;
			""")
			res = cursor.fetchall()
			print(res)
			conn.commit()
			
			deleteS3Object(key)
	finally:
		conn.close()
	
	return {"statusCode": 200, "body": "Query executed successfully"}