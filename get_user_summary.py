import json
import os

import boto3

from util import get_location_name


def get_user_summary(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    user_table = boto3.resource('dynamodb').Table(os.environ['USER_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    params = event['pathParameters']
    user = user_table.get_item(
        Key={'id': params['userId']}
    )
    wallet = wallet_table.scan(
        ConsistentRead=True,
        ScanFilter={
            'userId': {
                'AttributeValueList': [
                    params['userId']
                ],
                'ComparisonOperator': 'EQ'
            }
        }
    ).get('Items').pop()
    payment_history = history_table.scan(
        ScanFilter={
            'walletId': {
                'AttributeValueList': [
                    wallet['id']
                ],
                'ComparisonOperator': 'EQ'
            }
        }
    )
    sum_charge = 0
    sum_payment = 0
    times_per_location = {}
    for item in payment_history['Items']:
        sum_charge += item.get('chargeAmount', 0)
        sum_payment += item.get('useAmount', 0)
        location_name = get_location_name(item['locationId'])
        if location_name not in times_per_location:
            times_per_location[location_name] = 1
        else:
            times_per_location[location_name] += 1

    return {
        'statusCode': 200,
        'body': json.dumps({
            'userName': user['Item']['name'],
            'currentAmount': int(wallet['amount']),
            'totalChargeAmount': int(sum_charge),
            'totalUseAmount': int(sum_payment),
            'timesPerLocation': times_per_location
        })
    }
