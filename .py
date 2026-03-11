from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent 
env_path = BASE_DIR / '.env'

load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("BOT_TOKEN")
print("debug", TOKEN)