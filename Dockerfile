FROM python:3.6-slim

WORKDIR /app
ENTRYPOINT ["/app/cli.py"]

RUN apt-get update -y \
 && apt-get install -y \
   git \
 && apt-get clean -y

RUN pip install --upgrade pip

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .
