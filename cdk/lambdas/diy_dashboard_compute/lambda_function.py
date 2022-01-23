import json
import string
from unicodedata import category
import boto3
import requests
from botocore.exceptions import ClientError


class transaction:
    transaction_id: str
    description: str
    value: float
    date: str
    category: str
    parent_category: str
    table_name : str = 'diy_dashboard_up'

    def __init__(self, **kwargs):
        if kwargs.get('transaction_id'):
            self.transaction_id = kwargs.get('transaction_id')
        if kwargs.get('description'):
            self.description = kwargs.get('description')
        if kwargs.get('value'):
            self.value = kwargs.get('value')
        if kwargs.get('date'):
            self.date = kwargs.get('date')
        if kwargs.get('category'):
            self.category = kwargs.get('category')
        if kwargs.get('parent_category'):
            self.parent_category = kwargs.get('parent_category')
    
    def get(self):
        dictionary = {
            'transaction_id' : self.transaction_id,
            'description' : self.description,
            'value' : self.value,
            'date' : self.date,
            'category' : self.category,
            'parent_category' : self.parent_category
        }
        return dictionary
    
    def write_to_database(self, **kwargs):
        if kwargs.get('table_name'):
            self.table_name = kwargs.get('table_name')
        dynamodb = boto3.client('dynamodb')
        dynamodb.put_item(TableName=self.table_name, Item={'TransactionID':{'S': self.transaction_id},'Category':{'S': self.category}, 
        'ParentCategory' : {'S' : self.parent_category}, 'Value' : {'N' : self.value}, 'Description' : {'S' : self.description}, 
        'CreatedAt' : {'S' : self.date}})


    def get_from_database(self, **kwargs):
        if kwargs.get('table_name'):
            self.table_name = kwargs.get('table_name')
        dynamodb = boto3.client('dynamodb')
        dynamodb.get_item(TableName=self.table_name, Item={'TransactionID':{'S': self.transaction_id}})


class api_token:
    token_string : str
    secret_name : str = "diy_dashboard_up_api_key"
    region_name : str = "ap-southeast-2"


    def __init__(self, **kwargs):
        if kwargs.get('secret_name'):
            self.secret_name = kwargs.get('secret_name')

        if kwargs.get('region_name'):
            self.region_name = kwargs.get('region_name')

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=self.secret_name
            )
        except ClientError as e:
            raise e
        else:
            self.token_string = get_secret_value_response['SecretString']
        return self.token_string
    
    def get(self):
        dictionary = {
            'secret_name' : self.secret_name,
            'region_name' : self.region_name,
            'token_string' : self.token_string
        }

        return dictionary


class webhook:
    exists : bool
    api_invoke_url : str
    id : str

    def __init__(self, api_invoke_url):
        self.api_invoke_url = api_invoke_url
        headers = {'Authorization': 'Bearer {}'.format(api_token())}
        api_url = 'https://api.up.com.au/api/v1/webhooks' 
        data_object = {"data": {"attributes": {"url" : self.api_invoke_url}}}
        response = requests.post(api_url, headers=headers, json=data_object)
        if response.status_code == 200:
            self.exists = True
            self.id = response.get('data').get('id')
            print('Successfully created webhook: '.format(self.id))

    def get(self):
        dictionary = {
            'exists' : self.exists,
            'api_invoke_url' : self.api_invoke_url,
            'id' : self.id
        }

        return dictionary


def process_webhook(id):
    headers = {'Authorization': 'Bearer {}'.format(api_token())}
    api_url = 'https://api.up.com.au/api/v1/transactions/' + id 
    response = requests.get(api_url, headers=headers)
    data = response.json()
    transaction(
        transaction_id=id,
        description=data.get('data').get('attributes').get('description'),
        value=data.get('data').get('attributes').get('amount').get('value'),
        date=data.get('data').get('attributes').get('createdAt')
    )
    if data.get('data').get('relationships').get('category').get('data'):
        transaction(category=data.get('data').get('relationships').get('category').get('data').get('id'))
    else:
        transaction(category='Uncategorized')
    if data.get('data').get('relationships').get('parentCategory').get('data'):
        transaction(parent_category=data.get('data').get('relationships').get('parentCategory').get('data').get('id'))
    else:
        transaction(parent_category='Uncategorized')

    transaction.write_to_database()

    ##TODO Add reporting for pipeline before/after

def create_webhook(api_url):
    webhook(api_invoke_url=api_url)

    ##TODO Add reporting for pipeline before/after

def download_historical():
    headers = {'Authorization': 'Bearer {}'.format(api_token())}
    response = requests.get('https://api.up.com.au/api/v1/transactions', headers=headers)
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
    else:
        print(response.status_code)

    for array in data:
        for event in array:
            transaction(transaction_id=event.get('id'))
            transaction(description=event.get('attributes').get('description'))
            transaction(value=event.get('attributes').get('amount').get('value'))
            transaction(date=event.get('attributes').get('createdAt'))
            if event.get('relationships').get('category').get('data'):
                transaction(category=event.get('relationships').get('category').get('data').get('id'))
            else:
                transaction(category='Uncategorized')
            if event.get('relationships').get('parentCategory').get('data'):
                transaction(parent_category=event.get('relationships').get('parentCategory').get('data').get('id'))
            else:
                transaction(parent_category='Uncategorized')
        transaction.write_to_database()

    ##TODO Add reporting for pipeline before/after

    


def lambda_handler(event, context):
    print(event)
