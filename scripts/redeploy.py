"""Trigger a redeploy of the bolão site on BigBase."""
import httpx, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv(override=True)

r = httpx.post('https://bigbase.click/api/auth/login', json={
    'email': os.environ['BIGBASE_EMAIL'],
    'password': os.environ['BIGBASE_PASSWORD'],
}, timeout=10)
token = r.json()['token']

r2 = httpx.post(
    'https://bigbase.click/api/sites/04c58b9df51405ee33378c2539f9ea68/deploy',
    json={'branch': 'main', 'passthrough_paths': ['/api/version']},
    headers={'Authorization': f'Bearer {token}'},
    timeout=15,
)
if r2.status_code == 201:
    d = r2.json()
    print(f"Redeploy triggered! port={d['port']} status={d['status']} url=bolao.bigbase.click")
else:
    print(f"Error: {r2.status_code} {r2.text[:200]}")
    sys.exit(1)
