from confluent_kafka import Consumer
from utils import (
    get_env,
    get_logger,
    CustomMessage,
)

logger = get_logger(__name__)


def create_consumer(default_servers="localhost:9092", default_group_id="g1", default_offset="earliest"):
    conf = {
        "bootstrap.servers": get_env("KAFKA_BOOTSTRAP_SERVERS", default_servers),
        "group.id": get_env("KAFKA_GROUP_ID", default_group_id),
        "auto.offset.reset": get_env("KAFKA_AUTO_OFFSET_RESET", default_offset),
        "enable.auto.commit": get_env("KAFKA_ENABLE_AUTO_COMMIT", True),
    }
    return Consumer(conf)


def consume_messages(consumer, sec_between_poll=0.1):
    logger.info("⌛️ Waiting for messages...")

    while True:
        msg = consumer.poll(sec_between_poll)  # Ожидание сообщения с тайм-аутом

        if msg is None:
            continue

        if msg.error():
            logger.warning(f"🚫 Consume message error: {msg.error()}")
            continue

        key = msg.key().decode("utf-8") if msg.key() else None
        value = CustomMessage.from_json(msg.value().decode("utf-8"), logger) if msg.value() else None

        logger.info(f"✅ Consume message success: key={key}, value={value}, offset={msg.offset()}")


if __name__ == "__main__":
    consumer = create_consumer()
    topic_name = get_env("KAFKA_TOPIC", "default_topic")

    try:
        consumer.subscribe([topic_name])
        consume_messages(consumer)
    finally:
        consumer.close()
