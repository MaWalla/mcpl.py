FROM python:3.9
COPY . /app
RUN cd /app && pip install -r requirements.txt

ENTRYPOINT cd /app && gunicorn main:app -k flask_sockets.worker -w 1 --threads 1 -b 0.0.0.0:25576
