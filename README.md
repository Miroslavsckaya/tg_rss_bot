# Telegram RSS Bot

[![Build Status](https://ci.skobk.in/api/badges/Miroslavsckaya/tg_rss_bot/status.svg)](https://ci.skobk.in/Miroslavsckaya/tg_rss_bot)

## Setting up virtual environment

To be able to isolate project environment we'll use
[Python's venv](https://docs.python.org/3/library/venv.html).

### Setting up new environment and installing dependencies

```shell
# Create VirtualEnv directory
python -m venv ./.venv
# Loading environment
source .venv/bin/activate
# Installing dependencies
pip install -r requirements.txt
```

### Adding dependencies

```shell
# Installing new dependency
pip install somedependency
# Rewriting dependency file
pip freeze > requirements.txt
```

**Do not forget** to install the latest dependencies before adding new dependencies and rewriting
the `requirements.txt` file. Otherwise old dependencies could be lost.

## Running the bot

```shell
export RSSBOT_TG_TOKEN=xxx
export RSSBOT_DSN=xxx
python bot.py
```
## Running the update

```shell
export RSSBOT_TG_TOKEN=xxx
export RSSBOT_DSN=xxx
python update.py
```