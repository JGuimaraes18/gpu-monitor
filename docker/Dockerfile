FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && \
    apt-get install -y openssh-client gcc default-libmysqlclient-dev netcat-openbsd && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean

COPY . ./app

COPY docker/wait-for-mysql.sh /wait-for-mysql.sh

RUN chmod +x /wait-for-mysql.sh

CMD ["python", "-m", "app.main"]