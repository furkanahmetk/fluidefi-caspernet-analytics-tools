# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-bullseye as fluidefi-app

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# installing dependecies for installing python packages
RUN apt update -y && apt install -y build-essential libpq-dev
RUN pip install psycopg2-binary --no-binary psycopg2-binary

# installing packages
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN [ "python3", "-m", "pip", "install", "-r", "requirements.txt" ] 


# copying files & folders
COPY ./ ./
