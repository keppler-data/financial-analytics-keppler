# -*- coding: utf-8 -*-
"""
Celery Configuration for Distributed Task Queue
"""

from kombu import Exchange, Queue

# Broker settings
broker_url = 'amqp://guest:guest@rabbitmq:5672//'
result_backend = 'db+postgresql://airflow:airflow@postgres:5432/airflow'

# Task settings
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
worker_pool = 'prefork'
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'

# Task routing
task_routes = {
    'tasks.etl.*': {'queue': 'etl'},
    'tasks.elt.*': {'queue': 'elt'},
    'tasks.quality.*': {'queue': 'quality'},
    'tasks.diamond.*': {'queue': 'diamond'},
}

# Queue definitions
task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('etl', Exchange('etl'), routing_key='etl.*'),
    Queue('elt', Exchange('elt'), routing_key='elt.*'),
    Queue('quality', Exchange('quality'), routing_key='quality.*'),
    Queue('diamond', Exchange('diamond'), routing_key='diamond.*'),
)

# Task execution settings
task_track_started = True
task_send_sent_event = True
task_acks_late = True
worker_disable_rate_limits = True

# Retry settings
task_autoretry_for = (Exception,)
task_max_retries = 3
task_default_retry_delay = 60
