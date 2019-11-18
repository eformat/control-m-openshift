FROM registry.access.redhat.com/ubi8/python-36
#FROM python:3.7.5

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY runJob.py ./
COPY *.yaml ./

USER 1000
CMD python runJob.py -j $JOBNAME