FROM ubuntu:22.04

RUN apt update && apt install python3 python3-pip git -y

WORKDIR /src
COPY resolve.py requirements.txt /src

RUN pip install -r requirements.txt

CMD python3 /src/resolve.py
