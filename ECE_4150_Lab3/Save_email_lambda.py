import json
import boto3
import time


REGION="us-east-1"
dynamodb = boto3.resource('dynamodb',region_name=REGION)
SES=boto3.client('ses',region_name=REGION)
table = dynamodb.Table('AirQualityData')


def lambda_handler(event, context):
    # TODO implement
    time.sleep(2)
    print(event)
    timestamp=int(event['Records'][0]['dynamodb']['Keys']['timestamp']['N'])
    stationID=event['Records'][0]['dynamodb']['Keys']['stationID']['S']
    
    print(timestamp)
    print(stationID)
    response = table.query(
        KeyConditionExpression= boto3.dynamodb.conditions.Key('timestamp').eq(timestamp) & boto3.dynamodb.conditions.Key('stationID').eq(stationID)
        )
    
    print(response)
    items=response['Items']
    
    for item in items:
        if item['data']['so2']> .605 or item['data']['pm2_5']>250.4 or item['data']['pm10']>424 or item['data']['co']>30.4:
            response= SES.send_email(
                Destination={
                    'ToAddresses': ['zts929@gmail.com'],
                                    },
                        Message={
                            'Body': {
                                'Text':{
                                    'Data': "One or more of the tracked values is past dangerous values",
                                    },
                                },
                            'Subject':{
                                'Data': 'Warning'
                                },
                            },
                        Source='zts929@gmail.com')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
