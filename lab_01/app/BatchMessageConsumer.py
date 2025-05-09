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
        "enable.auto.commit": get_env("KAFKA_ENABLE_AUTO_COMMIT", False),

        "fetch.min.bytes": 10240,       # Минимум 10 KB данных за один poll
    }
    return Consumer(conf)


def consume_messages(consumer, sec_between_poll=1.0, batch_size=10):
    logger.info("⌛️ Waiting for messages...")

    while True:
        # Получить пакет сообщений
        messages = consumer.consume(batch_size, timeout=sec_between_poll)

        if not messages:
            continue

        for msg in messages:
            if msg.error():
                logger.warning(f"🚫 Consume message error: {msg.error()}")
                continue

            key = msg.key().decode("utf-8") if msg.key() else None
            value = CustomMessage.from_json(msg.value().decode("utf-8"), logger) if msg.value() else None

            logger.info(f"✅ Consume message success: key={key}, value={value}, offset={msg.offset()}")

        # После обработки всех сообщений коммитим оффсет
        try:
            consumer.commit(asynchronous=False)
            logger.info("✨ Offsets committed")
        except Exception as e:
            logger.error(f"🔥 Failed to commit offsets: {e}")


if __name__ == "__main__":
    consumer = create_consumer()
    topic_name = get_env("KAFKA_TOPIC", "default_topic")

    try:
        consumer.subscribe([topic_name])
        consume_messages(consumer)
    finally:
        consumer.close()
