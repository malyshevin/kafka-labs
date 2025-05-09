import time
from confluent_kafka import Producer
from utils import (
    get_env,
    get_logger,
    CustomMessage,
)

logger = get_logger(__name__)


def create_producer(default_servers="localhost:9092"):
    conf = {
        "bootstrap.servers": get_env("KAFKA_BOOTSTRAP_SERVERS", default_servers),
        "acks": "all",               # Гарантия того, что все реплики подтвердят получение
        "retries": 5,                # Количество повторных попыток в случае ошибки
        "enable.idempotence": True,  # Включаем идемпотентность для избежания дублирования
    }
    return Producer(conf)


def delivery_report(err, msg):
    if err is not None:
        logger.warning(f"🚫 Message delivery failed: {err}")
        return

    logger.info(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")


def produce_messages(producer, default_topic="default_topic", cnt_messages=100, ms_between_messages=0):
    topic_name = get_env("KAFKA_TOPIC", default_topic)

    for i in range(1, cnt_messages + 1):
        msg = CustomMessage(key=f"user_{i % 10}", value=f"Message {i}")
        serialized_msg = msg.to_json(logger)

        producer.produce(topic=topic_name, key=msg.key, value=serialized_msg, callback=delivery_report)
        producer.poll(0)  # Обработка коллбеков

        time.sleep(ms_between_messages)

    producer.flush()  # Ждет, пока все сообщения не будут переданы или обработаны


if __name__ == "__main__":
    producer = create_producer()
    produce_messages(producer)
