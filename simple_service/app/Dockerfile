FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && echo "Contents of requirements.txt:" \
    && cat /app/requirements.txt \
    && echo "Installed packages:" \
    && pip list

CMD ["python", "api.py"]