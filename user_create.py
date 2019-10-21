import json
import os

import boto3


def user_create(event, context):
    user_table = boto3.resource('dynamodb').Table(os.environ['USER_TABLE'])
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    body = json.loads(event['body'])
    user_table.put_item(
        Item={
            'id': body['id'],
            'name': body['name']
        }
    )
    wallet_table.put_item(
        Item={
            'id': body['id'],
            'userId': body['id'],
            'amount': 0
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps({'result': 'ok'})
    }
