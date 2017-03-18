FROM python:3.6
LABEL maintainer "Xi Shen <davidshen84@gmail.com>"

COPY requirements.txt /
RUN pip3 install --requirement /requirements.txt

COPY main/src /src

EXPOSE 80
WORKDIR /src
ENTRYPOINT ["python", "main.py"]
