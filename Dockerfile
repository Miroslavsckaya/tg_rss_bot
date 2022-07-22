FROM python:3.10-alpine

WORKDIR /bot

COPY . .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "python" ]

CMD [ "bot.py" ]