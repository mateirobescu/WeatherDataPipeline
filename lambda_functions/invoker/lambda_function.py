import json
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError


def lambda_handler(event, context):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table('OpenWeather-cities')
	lambda_client = boto3.client("lambda")
	
	cities_data = []
	last_key = None
	while True:
		scan_kwargs = {
			"FilterExpression": Attr("active").eq(True)
		}
		if last_key:
			scan_kwargs["ExclusiveStartKey"] = last_key
		
		try:
			response = table.scan(**scan_kwargs)
		except ClientError as e:
			print(f"DynamoDB scan failed: {e}")
			return {"statusCode": 500, "body": f"Scan failed: {e}"}
		
		cities_data.extend(response['Items'])
		last_key = response.get("LastEvaluatedKey")
		
		if last_key is None:
			break
	
	failures = 0
	for city in cities_data:
		city_data = {"city_id": city["ow-id"]}
		data_json = json.dumps(city_data)
		
		try:
			lambda_client.invoke(
				FunctionName="fetch-raw-weather-data--mateirobescu",
				InvocationType="Event",
				Payload=data_json
			)
		except ClientError as e:
			failures += 1
			print(f"Fetch for city {city_data["city_id"]} failed! - {e}")
	
	return {
		'statusCode': 200,
		'body': json.dumps(f"Invoke ended for {len(cities_data)} cities with {failures} failures.")
	}
