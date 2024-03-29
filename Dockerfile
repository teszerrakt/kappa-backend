FROM python:3.6-slim

COPY ./* ./app/
WORKDIR /app/

RUN pip install -r requirements.txt

EXPOSE 80

ENTRYPOINT ["bash", "/app/run.sh"]
