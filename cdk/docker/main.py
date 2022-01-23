import fastapi
import uvicorn as uvicorn
from unicodedata import category
from classes import webhook
from functions import download_historical, process_webhook


app = fastapi.FastAPI()

@app.post('/transaction')
def post_process_webhook(id):
    process_webhook(id)

@app.post('/webhook')
def post_create_webhook():
    create_webhook = webhook()

@app.post('/transaction/history')
def post_download_historical():
    download_historical()

@app.get('/')
def return_state():
    return {
        'web_server' : 'running'
    }
    
if __name__ == '__main__':
    uvicorn.run(app)
