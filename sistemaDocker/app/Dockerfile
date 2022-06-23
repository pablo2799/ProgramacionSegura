FROM python:3.9

RUN mkdir /code

WORKDIR /code

ADD requirements.txt /code/

RUN pip install -r requirements.txt

ENV SECRET_KEY=""
ENV DATABASE_NAME=""
ENV DATABASE_USER=""
ENV DATABASE_PASSWORD=""
ENV DATABASE_HOST=""
ENV DATABASE_PORT=3306

ADD run.sh /code/
RUN chmod +x run.sh

RUN mkdir /app
WORKDIR /app

RUN useradd usuario1 -s /bin/bash
RUN useradd limitado -m -s /bin/bash

ADD servidor.py /home/limitado
RUN mkdir /home/limitado/logs-socket
RUN chmod 777 /home/limitado/logs-socket

RUN chown -R usuario1 /code
RUN chmod -R 500 /code
RUN chown -R usuario1 /app

CMD /bin/bash -c '/code/run.sh'