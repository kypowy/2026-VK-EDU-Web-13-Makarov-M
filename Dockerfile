FROM python:3.12-slim

WORKDIR /app

# Отключаем создание .pyc и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ВАЖНО: Копируем содержимое папки web-qna в /app
COPY web-qna . 

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]