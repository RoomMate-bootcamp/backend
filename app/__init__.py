from os import getenv

from dotenv import load_dotenv

load_dotenv()

MONGO_DSN = getenv("MONGO_DSN")
ENVIRONMENT = getenv("ENVIRONMENT")
