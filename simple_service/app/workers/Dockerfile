FROM python:3.11-slim

WORKDIR /app/workers

COPY ./requirements.txt /app/workers/

RUN pip install --upgrade pip && \
    pip install -r /app/workers/requirements.txt && \
    pip install pydantic[email] && \
    pip install \
      --index-url https://download.pytorch.org/whl/cpu/ \
      --extra-index-url https://pypi.org/simple \
      torch==2.5.1 \
      torchvision==0.20.1

COPY . /app/workers/

# Устанавливаем переменную окружения PYTHONPATH
ENV PYTHONPATH=/app

CMD ["python", "worker.py"]
