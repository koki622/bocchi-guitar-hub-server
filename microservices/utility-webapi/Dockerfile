FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED 1
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm
ENV PATH /root/.local/bin:$PATH

RUN mkdir app

WORKDIR /app
COPY . .

RUN apt-get update &&\
    apt-get -y install locales ffmpeg &&\
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8

RUN pip install poetry &&\
    poetry config virtualenvs.create false &&\
    poetry lock &&\
    poetry install --no-root

ENV PYTHONPATH=/app
