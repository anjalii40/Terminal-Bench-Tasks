FROM python:3.10-slim

WORKDIR /app

RUN mkdir -p /app/state /app/input /app/output

COPY db.py /app/db.py
COPY snapshot.json /app/state/snapshot.json
COPY snapshot.json.bak /app/state/snapshot.json.bak
COPY wal.log.bak /app/state/wal.log.bak
RUN touch /app/state/wal.log

RUN pip install pytest==8.3.2 pytest-json-ctrf==0.3.5

CMD ["bash"]
