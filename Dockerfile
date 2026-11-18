FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SAVES_DIR=/data/saves

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py engine.py ./

# Сохранения игроков лежат здесь — подключите к этой папке постоянный диск (volume)
VOLUME ["/data"]

# Токен передаётся переменной окружения BOT_TOKEN
CMD ["python", "bot.py"]
