FROM python:3.10-slim
WORKDIR /app
COPY processor.py /app/processor.py
COPY config.json /app/config.json
RUN pip install pytest==8.3.2 pytest-json-ctrf==0.3.5
