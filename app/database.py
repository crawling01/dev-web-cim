import os
from dotenv import load_dotenv

# Load .env file based on environment
if os.getenv('DOCKER_DEPLOY') == 'true':
    load_dotenv('/app/.env')  # Path dalam container
else:
    load_dotenv()  # Untuk development lokal

_db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
