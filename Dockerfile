FROM python:2.7

WORKDIR /app

ADD anonymise.py ./anonymise.py
ADD requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

RUN chmod +x anonymise.py

CMD ["./anonymise.py"]
