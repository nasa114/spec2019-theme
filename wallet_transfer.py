import json
import os
from datetime import datetime

import boto3
import requests


def wallet_transfer(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    body = json.loads(event['body'])
    from_wallet = wallet_table.scan(
        ScanFilter={
            'userId': {
                'AttributeValueList': [
                    body['fromUserId']
                ],
                'ComparisonOperator': 'EQ'
            }
        }
    ).get('Items').pop()
    to_wallet = wallet_table.scan(
        ScanFilter={
            'userId': {
                'AttributeValueList': [
                    body['toUserId']
                ],
                'ComparisonOperator': 'EQ'
            }
        }
    ).get('Items').pop()

    from_total_amount = from_wallet['amount'] - body['transferAmount']
    to_total_amount = from_wallet['amount'] + body['transferAmount']
    if from_total_amount < 0:
        return {
            'statusCode': 400,
            'body': json.dumps({'errorMessage': 'There was not enough money.'})
        }

    wallet_table.update_item(
        Key={
            'id': from_wallet['id']
        },
        AttributeUpdates={
            'amount': {
                'Value': from_total_amount,
                'Action': 'PUT'
            }
        }
    )
    wallet_table.update_item(
        Key={
            'id': to_wallet['id']
        },
        AttributeUpdates={
            'amount': {
                'Value': to_total_amount,
                'Action': 'PUT'
            }
        }
    )
    history_table.put_item(
        Item={
            'walletId': from_wallet['id'],
            'transactionId': body['transactionId'],
            'useAmount': body['transferAmount'],
            'locationId': body['locationId'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    history_table.put_item(
        Item={
            'walletId': from_wallet['id'],
            'transactionId': body['transactionId'],
            'chargeAmount': body['transferAmount'],
            'locationId': body['locationId'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['fromUserId'],
        'useAmount': body['transferAmount'],
        'totalAmount': int(from_total_amount),
        'transferTo': body['toUserId']
    })
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['toUserId'],
        'chargeAmount': body['transferAmount'],
        'totalAmount': int(to_total_amount),
        'transferFrom': body['fromUserId']
    })

    return {
        'statusCode': 202,
        'body': json.dumps({'result': 'Assepted. Please wait for the notification.'})
    }
