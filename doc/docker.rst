Docker
======

Build docker image: ::

    docker build --tag weibo_stream .

Run docker image: ::

    docker run -d -P --name weibo_stream weibo_stream --weibo-access-token=some_token

Replace `some_token` with your Weibo API token.

Common Usage: ::

    curl --no-buffer --silent --get docker_host:port/public_timeline | tee -a status.log

This command will display the statuses on the console, and at the same time save the statuses to `status.log` file.

Unless the client close the connection, this request will never end, hence a **streaming** service.
However, if the remote API responds error, the service will close this connection.
