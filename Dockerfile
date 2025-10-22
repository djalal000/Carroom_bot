FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir python-telegram-bot==20.3 pillow dotenv

CMD ["python", "bot.py"]
