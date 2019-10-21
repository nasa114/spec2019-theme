import json
import os
from datetime import datetime

import boto3
import requests


def wallet_transfer(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    body = json.loads(event['body'])
    from_res = wallet_table.get_item(
        ConsistentRead=True,
        Key={
            'id': body['fromUserId']
        }
    )
    from_wallet = from_res['Item']

    from_total_amount = from_wallet['amount'] - body['transferAmount']
    transfer_amount = body['transferAmount']

    if from_total_amount < 0:
        return {
            'statusCode': 400,
            'body': json.dumps({'errorMessage': 'There was not enough money.'})
        }

    # TODO
    from_update_result = wallet_table.update_item(
        Key={
            'id': body['fromUserId']
        },
        UpdateExpression='SET amount = amount - :transfer_amount',
        ExpressionAttributeValues={
            ':transfer_amount': transfer_amount
        },
        ReturnValues="ALL_NEW",
    )

    # TODO
    to_update_result = wallet_table.update_item(
        Key={
            'id': body['toUserId']
        },
        UpdateExpression='SET amount = amount + :transfer_amount',
        ExpressionAttributeValues={
            ':transfer_amount': transfer_amount
        },
        ReturnValues="ALL_NEW",
    )

    # ここは数値を加算しないのでUpdateExpressionは要らなそう
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

    # 正しい値を入れる
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['fromUserId'],
        'useAmount': body['transferAmount'],
        'totalAmount': int(from_update_result['Attributes']['amount']),
        'transferTo': body['toUserId']
    })
    requests.post(os.environ['NOTIFICATION_ENDPOINT'], json={
        'transactionId': body['transactionId'],
        'userId': body['toUserId'],
        'chargeAmount': body['transferAmount'],
        'totalAmount': int(to_update_result['Attributes']['amount']),
        'transferFrom': body['fromUserId']
    })

    return {
        'statusCode': 202,
        'body': json.dumps({'result': 'Assepted. Please wait for the notification.'})
    }
