FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Long polling: nao precisa expor porta. Rode o seed uma vez antes (ver README).
CMD ["python", "-m", "bolao.bot"]
