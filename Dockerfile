FROM debian:bullseye
MAINTAINER me+docker@seth0r.net

RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get -y install vim python3-all python3-cherrypy3 python3-jinja2 python3-pymongo python3-requests python3-pip gpg wget gnupg2 curl procps

RUN pip3 install influxdb-client

EXPOSE 17485

ENV TMPSTOR /tmpstor
ENV PORT 17485
ENV RECVTHREADS 128

COPY *.py /code/
COPY parser /code/parser
COPY cron /code/cron

WORKDIR /code

CMD ["./main.py"]
