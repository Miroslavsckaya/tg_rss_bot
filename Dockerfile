FROM python:3.10-alpine

WORKDIR /bot

COPY . .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

# App settings
# https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
ENV RSSBOT_DSN=postgres://username:password@hostname/database_name
# https://core.telegram.org/bots#6-botfather
ENV RSSBOT_TG_TOKEN=1234567890:yourbotstoken
# https://docs.python.org/3/howto/logging.html#logging-levels
ENV LOG_LEVEL=INFO

ENTRYPOINT [ "python" ]

CMD [ "bot.py" ]