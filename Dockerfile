FROM python:3.9-buster
RUN pip install websockets mcrcon
RUN mkdir /app
COPY main.py /app/main.py

ENTRYPOINT python /app/main.py