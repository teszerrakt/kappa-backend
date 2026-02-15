FROM python:3.6-slim

COPY ./* ./app/
WORKDIR /app/

RUN pip install -r requirements.txt

ENV KAPPA_DB_PATH=/app/data/kappa.db
ENV PYTHONPATH=/app/src
RUN mkdir -p /app/data

VOLUME ["/app/data"]

EXPOSE 80

ENTRYPOINT ["bash", "/app/run.sh"]
