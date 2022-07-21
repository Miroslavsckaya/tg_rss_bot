FROM python:alpine

WORKDIR /bot

COPY . .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED='a'

ENTRYPOINT [ "python" ]

CMD [ "bot.py" ]