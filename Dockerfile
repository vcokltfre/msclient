FROM python:3.8

RUN mkdir /app

COPY . /app

WORKDIR /app

RUN pip install requirements.txt

CMD ["python", "main.py"]