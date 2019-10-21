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
        Key={
            'id': body['userId']
        }
    )
    user_wallet = result['Item']
    charge_amount = body['chargeAmount']

    update_result = wallet_table.update_item(
        Key={
            'id': user_wallet['id']
        },
        UpdateExpression='SET amount = amount - :charge_amount',
        ExpressionAttributeValues={
            ':charge_amount': charge_amount
        },
        ReturnValues="ALL_NEW",
    )

    # ここは数値を加算しないのでUpdateExpressionは要らなそう
    history_table.put_item(
        Item={
            'walletId': user_wallet['id'],
            'transactionId': body['transactionId'],
            'chargeAmount': body['chargeAmount'],
            'locationId': body['locationId'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

    # TODO updateの結果を正しく格納しないといけない
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['userId'],
        'chargeAmount': body['chargeAmount'],
        'totalAmount': int(update_result['Attributes']['amount'])
    })

    return {
        'statusCode': 202,
        'body': json.dumps({'result': 'Assepted. Please wait for the notification.'})
    }
