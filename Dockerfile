# Big Bolão — one image: Vue site built here, Python serves it and runs the bot.
FROM node:22-slim AS web
WORKDIR /src/web
ENV PUPPETEER_SKIP_DOWNLOAD=true
COPY web/package.json web/package-lock.json web/.npmrc ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
COPY VERSION /src/VERSION
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3000 \
    BOLAO_STORE=sqlite \
    BOLAO_DB=/data/bolao.db
WORKDIR /app
COPY requirements.txt ./
RUN grep -v -E '^pytest' requirements.txt > /tmp/req.txt \
    && pip install --no-cache-dir -r /tmp/req.txt && rm /tmp/req.txt
COPY VERSION app.py ./
COPY bolao/ bolao/
COPY --from=web /src/web/dist web/dist
RUN useradd --system --uid 1000 --no-create-home bolao \
    && mkdir /data && chown bolao /data
USER bolao
VOLUME /data
EXPOSE 3000
CMD ["python", "app.py"]
