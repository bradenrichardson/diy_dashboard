import json
import requests
import boto3
from botocore.exceptions import ClientError

def get_token():
    secret_name = "up_api_key"
    region_name = "ap-southeast-2"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    else:
        secret = get_secret_value_response['SecretString']
        return secret


def retrieve_transaction(transaction_id):
    api_url_base = 'https://api.up.com.au/api/v1/'
    headers = {'Authorization': 'Bearer {}'.format(get_token())}
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