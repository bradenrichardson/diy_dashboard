import httpx
from classes import transaction

async def process_webhook(id: str):

    headers = {f'Authorization': 'Bearer {api_token}'}
    api_url = 'https://api.up.com.au/api/v1/transactions/' + id 

    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(api_url, headers=headers)
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

async def download_historical():
    headers = {f'Authorization': 'Bearer {api_token}'}
    api_url = 'https://api.up.com.au/api/v1/transactions'

    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(api_url, headers=headers)

        data = []
        data.append(response.json().get('data'))
        if response.json().get('links').get('next'):
            token = response.json().get('links').get('next')
            while token:
                response = client.get(token, headers=headers)
                data.append(response.json().get('data'))
                token = response.json().get('links').get('next')
                if token:
                    print("Processing token: {}".format(token))
                else:
                    print("Finished processing tokens")

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