
import json
import os
import pika


QUEUE_NAME = "inventory_events"


def publish_event(event: dict) -> None:
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "warehouse"),
        os.getenv("RABBITMQ_PASSWORD", "warehouse_dev"),
    )

    params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        port=5672,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=5,
        connection_attempts=3,
        retry_delay=1,
    )

    connection = pika.BlockingConnection(params)

    try:
        channel = connection.channel()

        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True,
        )

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(event).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
    finally:
        connection.close()
