FROM nvidia/cuda:12.4.0-base-ubuntu20.04

ENV PYTHONUNBUFFERED 1
ENV PATH /root/.local/bin:$PATH
ENV TZ=Asia/Tokyo

RUN mkdir app &&\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY . .

RUN apt-get update &&\
    apt install -y pip python3.9 &&\
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

RUN pip install poetry
    #poetry config virtualenvs.create false
    #poetry install

    #apt install -y python3.9 &&\
    #apt-get -y install pip &&\
    #pip3 install poetry
    #apt-get -y install python3 curl &&\
    #curl -sSL https://install.python-poetry.org | python3 -
    #poetry install

