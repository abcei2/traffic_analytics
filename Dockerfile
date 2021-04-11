FROM jjanzic/docker-python3-opencv
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
COPY ./requirements.txt /opt/app/
WORKDIR /opt/app/
RUN pip install -r requirements.txt
WORKDIR /opt/app/traffic_analytics