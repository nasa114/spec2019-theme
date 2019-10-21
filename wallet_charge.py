import json
import os
from datetime import datetime

import boto3
import requests


def wallet_charge(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    body = json.loads(event['body'])
    result = wallet_table.get_item(
        Key = {
            'id': body['userId']
        }
    )
    user_wallet = result['Item']
    total_amount = user_wallet['amount'] + body['chargeAmount']
    wallet_table.update_item(
        Key={
            'id': user_wallet['id']
        },
        AttributeUpdates={
            'amount': {
                'Value': total_amount,
                'Action': 'PUT'
            }
        }
    )
    history_table.put_item(
        Item={
            'walletId': user_wallet['id'],
            'transactionId': body['transactionId'],
            'chargeAmount': body['chargeAmount'],
            'locationId': body['locationId'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['userId'],
        'chargeAmount': body['chargeAmount'],
        'totalAmount': int(total_amount)
    })

    return {
        'statusCode': 202,
        'body': json.dumps({'result': 'Assepted. Please wait for the notification.'})
    }
