FROM python:3.6
MAINTAINER Xi Shen <davidshen84@gmail.com>

COPY requirements.txt /app/
RUN pip install --requirement /app/requirements.txt

COPY main.py /app/

EXPOSE 80
WORKDIR /app
ENTRYPOINT ["python", "main.py"]
