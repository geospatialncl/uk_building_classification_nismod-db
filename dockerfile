FROM python:3.8

RUN pip3 install geopandas requests psycopg2
COPY building_classification.py .
COPY run_building_classification.py /run.py
COPY init.txt .

CMD ["python", "run.py"]