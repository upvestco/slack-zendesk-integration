FROM --platform=linux/amd64 python:3.10.10-slim-bullseye

# TODO How strict do we have to be with the version pinning?
# The desired install is `libpq5`. (For `psycopg`.) All others are 2nd level dependencies.
RUN apt-get update \
    && \
    apt-get install -y \
    libsasl2-modules-db=2.1.27+dfsg-2.1+deb11u1 \
    libsasl2-2=2.1.27+dfsg-2.1+deb11u1 \
    libldap-2.4-2=2.4.57+dfsg-3+deb11u1 \
    libldap-common=2.4.57+dfsg-3+deb11u1 \
    libpq5=13.10-0+deb11u1 \
    libsasl2-modules=2.1.27+dfsg-2.1+deb11u1 \
    && \
    apt clean

COPY ./app.py /work/app.py
COPY ./config.py /work/config.py
COPY ./settings.py /work/settings.py
COPY ./requirements.txt /work/requirements.txt

WORKDIR /work/

RUN pip install -r requirements.txt

ENTRYPOINT ["/usr/local/bin/python", "/work/app.py"]
