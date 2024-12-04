# Running the Code

1. Download docker desktop at https://www.docker.com/ (recommended settings during installation will suffice)

2. Install RabbitMQ in docker

```docker pull rabbitmq:management``` into console

```docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management``` into console


3. set up docker cluster

```docker-compose up --scale worker=<num_of_workers>```

4. on another terminal

```docker exec -it <container_name> bash```

Note: you can use ```docker ps``` to look for active containers

5. Once in, type:

```python -m celery_main.task_submitter <url> <time_Limit> <Num_nodes>```

# Extras

1. rebuilding of containers
```docker-compose down``` first to remove existing containers before rebuilding set up of docker cluster

2. rabbitmq browser view at localhost:15672

# Source
1. https://pythoncircle.com/post/518/scraping-10000-tweets-in-60-seconds-using-celery-rabbitmq-and-docker-cluster-with-rotating-proxy/
2. https://docs.docker.com/desktop/setup/install/windows-install/
3. https://hub.docker.com/_/rabbitmq