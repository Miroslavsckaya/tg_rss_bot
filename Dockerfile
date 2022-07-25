FROM python:3.10-alpine

WORKDIR /bot

COPY . .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

# App settings
ENV RSSBOT_DSN=xxx
ENV RSSBOT_TG_TOKEN=xxx
ENV LOG_LEVEL=INFO

ENTRYPOINT [ "python" ]

CMD [ "bot.py" ]