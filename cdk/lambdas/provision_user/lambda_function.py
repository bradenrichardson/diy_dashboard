import json
import boto3
import requests
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

api_url_base = 'https://api.up.com.au/api/v1/'
headers = {'Authorization': 'Bearer {}'.format(get_token())}

def create_webhook(invoke_url):
    api_url = api_url_base + 'webhooks' 
    data_object = {"data": {"attributes": {"url" : invoke_url}}}
    response = requests.post(api_url, headers=headers, json=data_object)
    print(response.text)

def create_list(api_url):
    response = requests.get(api_url, headers=headers)
    print(response)
    if response.status_code == 200:
        data = []
        data.append(response.json().get('data'))
        if response.json().get('links').get('next'):
            token = response.json().get('links').get('next')
            while token:
                response = requests.get(token, headers=headers)
                data.append(response.json().get('data'))
                token = response.json().get('links').get('next')
                if token:
                    print("Processing token: {}".format(token))
                else:
                    print("Finished processing tokens")
        return data
    else:
        print(response.status_code)

def create_Dictionary():
    api_url = api_url_base + 'transactions'
    data = create_list(api_url)
    csvDictionary = {'id' : [], 'description' : [], 'value' : [], 'category' : [], 'parentCategory' : [], 'createdAt' : []}

    for array in data:
        for transaction in array:
            csvDictionary['id'].append(transaction.get('id'))
            csvDictionary['description'].append(transaction.get('attributes').get('description'))
            csvDictionary['value'].append(transaction.get('attributes').get('amount').get('value'))
            if transaction.get('relationships').get('category').get('data'):
                csvDictionary['category'].append(transaction.get('relationships').get('category').get('data').get('id'))
            else:
                csvDictionary['category'].append('Uncategorized')
            if transaction.get('relationships').get('parentCategory').get('data'):
                csvDictionary['parentCategory'].append(transaction.get('relationships').get('parentCategory').get('data').get('id'))
            else:
                csvDictionary['parentCategory'].append('Uncategorized')
            csvDictionary['createdAt'].append(transaction.get('attributes').get('createdAt'))
                
    return csvDictionary

def write_to_dynamo():
    dictionary = create_Dictionary()
    dynamodb = boto3.client('dynamodb')
    a = 0
    for transaction in dictionary['id']:
        dynamodb.put_item(TableName='diy_dashboard_up', Item={'TransactionID':{'S': dictionary['id'][a]},'Category':{'S': dictionary['category'][a]}, 
        'ParentCategory' : {'S' : dictionary['parentCategory'][a]}, 'Value' : {'N' : dictionary['value'][a]}, 'Description' : {'S' : dictionary['description'][a]}, 
        'CreatedAt' : {'S' : dictionary['createdAt'][a]}})
        a += 1


def lambda_handler(event, context):
    write_to_dynamo()
