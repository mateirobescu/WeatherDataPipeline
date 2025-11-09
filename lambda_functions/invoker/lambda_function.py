import json
import boto3
from boto3.dynamodb.conditions import Attr


def lambda_handler(event, context):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table('OpenWeather-cities')
	
	response = table.scan(
		FilterExpression=Attr('active').eq(True)
	)
	cities_data = response['Items']
	
	lambda_client = boto3.client("lambda")
	
	for city in cities_data:
		city_data = {"city_id": city["ow-id"]}
		data_json = json.dumps(city_data)
		
		lambda_client.invoke(
			FunctionName="fetch-raw-weather-data--mateirobescu",
			InvocationType="Event",
			Payload=data_json
		)
	
	return {
		'statusCode': 200,
		'body': json.dumps("Invoke ended.")
	}
