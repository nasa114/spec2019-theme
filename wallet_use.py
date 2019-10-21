import json
import os
from datetime import datetime

import boto3
import requests


def wallet_use(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    body = json.loads(event['body'])
    result = wallet_table.get_item(
        ConsistentRead=True,
        Key={
                'id': body['userId']
        }
    )
    user_wallet = result['Item']
    expected_total_amount = user_wallet['amount'] - body['useAmount']
    use_amount = body['useAmount']

    if expected_total_amount < 0:
        return {
            'statusCode': 400,
            'body': json.dumps({'errorMessage': 'There was not enough money.'})
        }

    # 数値の更新はUpdateExpressionする
    update_result = wallet_table.update_item(
        Key={
            'id': user_wallet['id']
        },
        # "In general, we recommend using SET rather than ADD" in the doc
        UpdateExpression='SET amount = amount - :use_amount',
        ExpressionAttributeValues={
            ':use_amount': {'N': use_amount}
        },
        ReturnValue="ALL_NEW",
    )
    print(update_result) # FIXME

    # ここは数値を加算しないのでUpdateExpressionは要らなそう
    history_table.put_item(
        Item={
            'walletId': user_wallet['id'],
            'transactionId': body['transactionId'],
            'useAmount': body['useAmount'],
            'locationId': body['locationId'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['userId'],
        'useAmount': body['useAmount'],
        'totalAmount': int(update_result['Attributes']['amount']['N'])
    })

    return {
        'statusCode': 202,
        'body': json.dumps({'result': 'Assepted. Please wait for the notification.'})
    }
