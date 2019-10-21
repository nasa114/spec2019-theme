import json
import os
from datetime import datetime

import boto3
import requests


def wallet_charge(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    body = json.loads(event['body'])
    charge_amount = body['chargeAmount']

    print(json.dumps(body))  # DEBUG

    update_result = wallet_table.update_item(
        Key={
            'id': body['userId']
        },
        UpdateExpression='SET amount = amount + :charge_amount',
        ExpressionAttributeValues={
            ':charge_amount': charge_amount
        },
        ReturnValues="ALL_NEW",
    )

    print(f'update_result: {json.dumps(update_result)}')  # DEBUG

    # ここは数値を加算しないのでUpdateExpressionは要らなそう
    history_table.put_item(
        Item={
            'walletId': body['userId'],
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
