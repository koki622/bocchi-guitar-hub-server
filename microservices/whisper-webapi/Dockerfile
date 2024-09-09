FROM nvidia/cuda:12.4.0-base-ubuntu20.04

ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Tokyo
ENV PATH /root/.local/bin:$PATH

RUN mkdir app &&\
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY . .

RUN apt-get update &&\
    apt install -y python3.9 python3.9-distutils ffmpeg curl git &&\
    curl -sSL https://install.python-poetry.org | python3.9 -
    

RUN poetry config virtualenvs.create false &&\
    poetry lock &&\
    poetry install &&\
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

ENV PYTHONPATH /usr/lib/python3.9/site-packages:$PYTHONPATH
#ENV TORCH_CUDNN_V8_API_DISABLED=1
