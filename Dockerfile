# Base Image
FROM ubuntu:20.04

# maintainer info
MAINTAINER "morgan@grepp.co"

# setting timezone
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# env setting & compiler installation
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        python3.8 \
        manpages-dev \
        openjdk-11-jdk \
        curl \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -

RUN apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# copy TCH project to Docker's /TCH directory
COPY . /TCH

# cd /TCH
WORKDIR /TCH

# running command when container is started
ENTRYPOINT [ "python3", "run.py" ]