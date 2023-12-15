import os
import urllib.parse

PORT=int(os.environ.get("PORT"))

SLACK_CLIENT_ID = os.environ["SLACK_CLIENT_ID"]
SLACK_CLIENT_SECRET = os.environ["SLACK_CLIENT_SECRET"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]
POSTGRES_DATABASE = os.environ["POSTGRES_DATABASE"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

postgres_password_quoted = urllib.parse.quote(POSTGRES_PASSWORD, safe='')
if POSTGRES_HOST.startswith("/cloudsql/"):
    # GCP Cloud Run provides a connection to a SQL instance as a Unix named pipe, whose filename starts with "/cloudsql/"
    # See https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    # See https://stackoverflow.com/a/54967705
    DB_CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{postgres_password_quoted}@/{POSTGRES_DATABASE}?host={POSTGRES_HOST}"
else:
    DB_CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{postgres_password_quoted}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"
