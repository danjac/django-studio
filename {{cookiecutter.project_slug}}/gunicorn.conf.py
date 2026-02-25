import multiprocessing

# https://docs.gunicorn.org/en/stable/configure.html#configuration-file

wsgi_app = "config.asgi"

loglevel = "info"

accesslog = "-"
access_log_format = '%(t)s %(h)s - "%(r)s" %(s)s %(L)s'

errorlog = "-"

timeout = 30
graceful_timeout = timeout + 10

worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() + 1

max_requests = 1000
max_requests_jitter = 50
