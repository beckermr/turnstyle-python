# Container image that runs your code
FROM python:3.8-alpine

RUN pip install pygithub -y

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY entrypoint.sh /entrypoint.sh
COPY turnstyle.py /turnstyle.py

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]
