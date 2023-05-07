# syntax=docker/dockerfile:1
FROM python:3.12-rc-slim

ENV PYTHONUNBUFFERED 1

# install app dependencies
RUN apt-get update && apt-get install -y python3 python3-pip

# install app
RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt requirements.txt
COPY entrypoint.sh /app/entrypoint.sh
COPY BASD /app
RUN pip install -r requirements.txt

CMD sh entrypoint.sh
