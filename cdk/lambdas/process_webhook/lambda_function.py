import json
import requests
import os
import boto3

api_token = os.getenv('api_token')
api_url_base = 'https://api.up.com.au/api/v1/'
headers = {'Authorization': 'Bearer {}'.format(api_token)}

def retrieve_transaction(transaction_id):
    api_url = api_url_base + 'transactions/' + transaction_id 
    response = requests.get(api_url, headers=headers)
    data = response.json()
    dictionary = {
        'ID' : transaction_id,
        'Description' : data.get('data').get('attributes').get('description'),
        'Value' : data.get('data').get('attributes').get('amount').get('value'),
        'CreatedAt' : data.get('data').get('attributes').get('createdAt')
    }
    if data.get('data').get('relationships').get('category').get('data'):
        dictionary['Category'] = data.get('data').get('relationships').get('category').get('data').get('id')
    else:
        dictionary['Category'] = 'Uncategorized'
    if data.get('data').get('relationships').get('parentCategory').get('data'):
        dictionary['ParentCategory'] = data.get('data').get('relationships').get('parentCategory').get('data').get('id')
    else:
        dictionary['ParentCategory'] = 'Uncategorized'
    return dictionary


def write_to_dynamo(dictionary):
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(TableName='quicksightTest', Item={'TransactionID':{'S': dictionary['ID']},'Category':{'S': dictionary['Category']}, 
    'ParentCategory' : {'S' : dictionary['ParentCategory']}, 'Value' : {'N' : dictionary['Value']}, 'Description' : {'S' : dictionary['Description']}, 
    'CreatedAt' : {'S' : dictionary['CreatedAt']}})


def lambda_handler(event, context):
    load_body = json.loads(event.get('body'))
    transaction_id = load_body.get('data').get('relationships').get('transaction').get('data').get('id')
    transaction = retrieve_transaction(transaction_id)
    write_to_dynamo(transaction)