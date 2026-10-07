import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
if not url or not key:
    raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set')

supabase: Client = create_client(url, key)