
import json
import os
import time
import pika
from datetime import datetime, timezone


QUEUE_NAME = "inventory_events"


def main():
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
    )

    # RabbitMQ puede estar "healthy" antes de aceptar conexiones AMQP:
    # reintentamos en vez de morir en el primer fallo.
    connection = None
    for attempt in range(1, 31):
        try:
            connection = pika.BlockingConnection(params)
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"RabbitMQ no disponible (intento {attempt}/30), reintentando en 2s...", flush=True)
            time.sleep(2)
    if connection is None:
        raise SystemExit("No se pudo conectar a RabbitMQ")

    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
    )

    channel.basic_qos(prefetch_count=1)

    def process_message(ch, method, properties, body):
        try:
            event = json.loads(body.decode("utf-8"))

            print(
                f"[{datetime.now(timezone.utc).isoformat()}] "
                f"Procesando evento: {event}",
                flush=True,
            )

            # Aquí irá el trabajo real de auditoría,
            # estadísticas u otra tarea secundaria.

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except (ValueError, UnicodeDecodeError) as exc:
            print(f"Mensaje inválido: {exc}", flush=True)

            # En esta primera versión descartamos el
            # mensaje inválido después de registrarlo.
            # En una fase posterior implementaremos una DLQ.
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=process_message,
        auto_ack=False,
    )

    print(f"Worker escuchando la cola: {QUEUE_NAME}", flush=True)

    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
