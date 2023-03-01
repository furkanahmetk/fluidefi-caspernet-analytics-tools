# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-bullseye as base

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
COPY ./cspr_summarization/entities ./cspr_summarization/entities
COPY ./cspr_summarization/migrations ./cspr_summarization/migrations
COPY ./cspr_summarization/services/lp_block_summarizer ./cspr_summarization/services/lp_block_summarizer
COPY ./manage.py ./manage.py
COPY ./settings.py ./settings.py
COPY ./block_summarizer.py ./block_summarizer.py 

ARG READ_DB_CONNECTION_HOST
ENV READ_DB_CONNECTION_HOST=$READ_DB_CONNECTION_HOST

ARG READ_DB_CONNECTION_DATABASE
ENV READ_DB_CONNECTION_DATABASE=$READ_DB_CONNECTION_DATABASE

ARG READ_DB_CONNECTION_USERNAME
ENV READ_DB_CONNECTION_USERNAME=$READ_DB_CONNECTION_USERNAME

ARG READ_DB_CONNECTION_PASSWORD
ENV READ_DB_CONNECTION_PASSWORD=$READ_DB_CONNECTION_PASSWORD

ARG READ_DB_CONNECTION_PORT
ENV READ_DB_CONNECTION_PORT=$READ_DB_CONNECTION_PORT

ARG WRITE_DB_CONNECTION_HOST
ENV WRITE_DB_CONNECTION_HOST=$WRITE_DB_CONNECTION_HOST

ARG WRITE_DB_CONNECTION_DATABASE
ENV WRITE_DB_CONNECTION_DATABASE=$WRITE_DB_CONNECTION_DATABASE

ARG WRITE_DB_CONNECTION_USERNAME
ENV WRITE_DB_CONNECTION_USERNAME=$WRITE_DB_CONNECTION_USERNAME

ARG WRITE_DB_CONNECTION_PASSWORD
ENV WRITE_DB_CONNECTION_PASSWORD=$WRITE_DB_CONNECTION_PASSWORD

ARG WRITE_DB_CONNECTION_PORT
ENV WRITE_DB_CONNECTION_PORT=$WRITE_DB_CONNECTION_PORT

#  Run Migrations and then start the service
ENTRYPOINT ["/bin/sh", "-c", "python3 manage.py migrate cspr_summarization && python3 block_summarizer.py" ] 



