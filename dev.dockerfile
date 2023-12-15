FROM python:3.10.10-slim-bullseye

RUN apt-get update \
    && \
    apt-get install -y \
    bash \
    curl \
    make \
    vim \
    postgresql-client-13 \
    && \
    apt clean

WORKDIR /work/

ENTRYPOINT ["bash"]
