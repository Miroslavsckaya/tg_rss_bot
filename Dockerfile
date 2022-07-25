FROM python:3.10-alpine

WORKDIR /bot

COPY . .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1 RSSBOT_DSN=xxx RSSBOT_TG_TOKEN=xxx LOG_LEVEL=INFO

ENTRYPOINT [ "python" ]

CMD [ "bot.py" ]