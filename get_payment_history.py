import json
import os

import boto3

from util import get_location_name


def get_payment_history(event, context):
    wallet_table = boto3.resource('dynamodb').Table(os.environ['WALLET_TABLE'])
    history_table = boto3.resource('dynamodb').Table(os.environ['PAYMENT_HISTORY_TABLE'])
    params = event['pathParameters']
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
    payment_history_result = history_table.scan(
        ScanFilter={
            'walletId': {
                'AttributeValueList': [
                    wallet['id']
                ],
                'ComparisonOperator': 'EQ'
            }
        }
    )

    payment_history = []
    for p in payment_history_result['Items']:
        if 'chargeAmount' in p:
            p['chargeAmount'] = int(p['chargeAmount'])
        if 'useAmount' in p:
            p['useAmount'] = int(p['useAmount'])
        p['locationName'] = get_location_name(p['locationId'])
        del p['locationId']
        payment_history.append(p)

    sorted_payment_history = list(sorted(
        payment_history,
        key=lambda x: x['timestamp'],
        reverse=True))

    return {
        'statusCode': 200,
        'body': json.dumps(sorted_payment_history)
    }
