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