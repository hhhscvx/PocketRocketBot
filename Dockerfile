FROM python:3.11-slim

COPY requirements.txt /temp/requirements.txt

RUN pip install -r /temp/requirements.txt

COPY . /code

WORKDIR /code

CMD ["python3", "main.py", "-a", "2"]
