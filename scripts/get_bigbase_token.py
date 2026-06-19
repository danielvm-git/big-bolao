#!/usr/bin/env python3
"""Obtem um token JWT do BigBase usando as credenciais do bot e grava no .env do web."""
import os, sys
# Add project root to path so 'bolao' package can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from bolao.config import BIGBASE_URL, BIGBASE_EMAIL, BIGBASE_PASSWORD
import httpx, asyncio

ENV_PATH = os.path.join(os.path.dirname(__file__), "web", ".env")

async def main():
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{BIGBASE_URL}/api/auth/login",
            json={"email": BIGBASE_EMAIL, "password": BIGBASE_PASSWORD},
        )
        r.raise_for_status()
        token = r.json()["token"]
        print(f"✅ JWT obtido de {BIGBASE_URL}")
        print(f"   Token: {token[:20]}...{token[-10:]}")
        
        # Read existing .env if any
        existing = {}
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        existing[k] = v
        
        existing['VITE_BIGBASE_URL'] = BIGBASE_URL
        existing['VITE_BIGBASE_TOKEN'] = token
        
        with open(ENV_PATH, 'w') as f:
            for k, v in existing.items():
                f.write(f"{k}={v}\n")
        
        print(f"   .env gravado em {ENV_PATH}")
        print(f"\nVariáveis: {', '.join(existing.keys())}")

if __name__ == '__main__':
    asyncio.run(main())
