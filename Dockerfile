ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 py3-pip
    #nodejs npm

# Python 3 HTTP Server serves the current working dir
# So let's set it to our add-on persistent data directory.
WORKDIR /

# Copy data for add-on
COPY . /
RUN chmod a+x /run.sh
RUN chmod 777 /run.sh

RUN pip3 install python-selve-new
RUN pip3 install requests
RUN pip3 install flask
RUN pip3 install Flask-Cors

RUN pip3 show python-selve-new

WORKDIR /frontend

#RUN npm install
#RUN npm run build

WORKDIR /

CMD [ "/run.sh" ]