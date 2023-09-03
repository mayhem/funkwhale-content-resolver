FROM ubuntu:22.04

RUN apt update && apt install python3 python3-pip git -y

WORKDIR /src
COPY requirements.txt /src/

RUN pip install -r requirements.txt

COPY resolve.py /src/
CMD flask --app resolve run --host=0.0.0.0 --port 5001
