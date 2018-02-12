FROM python:3.6-slim
MAINTAINER Yusuf Iqbal <yusuf.iqbal@devfactory.com>

# Set the application directory
WORKDIR /app

# Install our requirements.txt
ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy code from the current folder to /app inside the container
ADD . /app

RUN mkdir ~/.aws
RUN cp /app/credentials ~/.aws/credentials
RUN cp /app/config ~/.aws/config
