import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE = os.path.join(os.getcwd(), 'helpdesk.db')
