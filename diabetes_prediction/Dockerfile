FROM ubuntu:latest

# Setting work Directory
WORKDIR /app

# Setting ENV Variables
ENV VENV /opt/venv
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONPATH /app

# Setting up proxy 
ENV http_proxy http://proxy.accounts.intern:8081/
ENV https_proxy http://proxy.accounts.intern:8081/
ENV HTTP_PROXY http://proxy.accounts.intern:8081/
ENV HTTPS_PROXY http://proxy.accounts.intern:8081/

# Update ubuntu dependencies
RUN : \
    && apt-get update \
    && apt-get install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa


# Installing python
RUN : \
    && apt-get update \
    && apt-get install python3 python3-pip python3-venv make build-essential libssl-dev curl vim -y


# Things for opencv
RUN apt-get update && apt-get install -y libsm6 libxext6 libxrender-dev ffmpeg


# Install AWS CLI
RUN pip3 install awscli

WORKDIR /opt
RUN curl -k https://sdk.cloud.google.com > install.sh
RUN bash /opt/install.sh --install-dir=/opt
ENV PATH $PATH:/opt/google-cloud-sdk/bin

WORKDIR /app


# Virtual Environment
ENV VENV /opt/venv
RUN python3 -m venv ${VENV}

ENV PATH="${VENV}/bin:$PATH"



# Install Python Dependencies
COPY requirements.txt /app
RUN ${VENV}/bin/pip install -r /app/requirements.txt

# Copy Actual Code
COPY . /app

# Copy over the helper script
RUN cp ${VENV}/bin/flytekit_venv /usr/local/bin/
RUN chmod a+x /usr/local/bin/flytekit_venv

# Flyte Configuration
ARG tag
ENV FLYTE_INTERNAL_IMAGE $tag
