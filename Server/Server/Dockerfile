ARG TENSORFLOW_ARG_TAGS=
FROM tensorflow/tensorflow:latest${TENSORFLOW_ARG_TAGS}-py3
WORKDIR /anopcb-server
COPY pip_requirements_docker.txt .
RUN pip install -r pip_requirements_docker.txt
COPY . .
CMD [ "python", "-u", "AnomalyServer.py", "--local", "23923"]