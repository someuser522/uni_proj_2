FROM python:3.8

WORKDIR /telegram_bot

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD [ "python3", "app.py"]