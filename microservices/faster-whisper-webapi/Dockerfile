FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Tokyo
ENV PATH /root/.local/bin:$PATH

RUN mkdir app &&\
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY . .

RUN apt-get update &&\
    apt install -y python3 python3-distutils ffmpeg curl git &&\
    curl -sSL https://install.python-poetry.org | python3 -

RUN poetry config virtualenvs.create false &&\
    poetry lock &&\
    poetry install --no-root