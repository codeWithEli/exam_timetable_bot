# use base image that comes with chromedriver preinstalled
FROM selenium/standalone-chrome

# switch to  root user for installation
USER root

# set working directory
WORKDIR /home/app

# install python, pip, venv
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*

# copy dependency list
COPY requirements.txt .

# create virtual environment
RUN python3 -m venv /opt/venv && . /opt/venv/bin/activate && \
# install dependencies in a virtual environment
pip install --no-cache-dir -r requirements.txt

# update python path to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# copy src code
COPY ./src /home/app/src
COPY ./serviceAccount.json .

# switch back to app user
USER seluser

# run app
CMD python3 src/main.py