import time
import json
from kafka import KafkaProducer, KafkaConsumer
from services.utils import logger, get_env


def create_producer(servers="localhost:9092"):
    conf = {
        "bootstrap_servers": get_env("KAFKA_BOOTSTRAP_SERVERS", servers),
        "acks": "all",
        "retries": 5,
        "enable_idempotence": True,
        "value_serializer": lambda v: v.encode('utf-8') if v else None,
        "key_serializer": lambda v: v.encode('utf-8') if v else None,
    }
    return KafkaProducer(**conf)


def create_consumer(topic, default_servers="localhost:9092", default_group_id="g1"):
    conf = {
        "bootstrap_servers": get_env("KAFKA_BOOTSTRAP_SERVERS", default_servers),
        "group_id": get_env("KAFKA_GROUP_ID", default_group_id),
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
        "value_deserializer": lambda v: v.decode("utf-8") if v else None,
        "key_deserializer": lambda v: v.decode("utf-8") if v else None,
    }
    return KafkaConsumer(topic, **conf)


def send_chat_message(producer, from_id, to_id, text):
    key = to_id 
    value = json.dumps({
        "from_id": from_id,
        "to_id": to_id,
        "text": text
    })
    future = producer.send("messages", key=key, value=value)
    future.get(timeout=10)
    logger.info(f"Chat message sent: {value}")


def send_block_user_message(producer, user_id, blocked_user_id, action):
    key = user_id
    value = json.dumps({
        "user_id": user_id,
        "blocked_user_id": blocked_user_id,
        "action": action  # 'add' или 'remove'
    })
    topic = "blocked_users"
    producer.partitions_for(topic)  # гарантируем, что метаданные прогружены
    partitions = producer.partitions_for(topic)

    for partition in partitions:
        future = producer.send(topic, key=key, value=value, partition=partition)
        future.get(timeout=10)
    logger.info(f"Block user message sent: {value}")


def send_ban_word_message(producer, word, action):
    key = word
    value = json.dumps({
        "word": word,
        "action": action
    })
    topic = "banned_words"
    producer.partitions_for(topic)
    partitions = producer.partitions_for(topic)

    for partition in partitions:
        future = producer.send(topic, key=key, value=value, partition=partition)
        future.get(timeout=10)
    logger.info(f"Ban word message sent: {value}")


def receive_chat_message(consumer):
    logger.info("⌛️ Waiting for filtered messages...")
    try:
        for msg in consumer:
            try:
                value = json.loads(msg.value)
            except Exception as e:
                logger.error(f"JSON load error: {e}")
                continue
            yield msg.key, value
    except Exception as e:
        logger.error(f"Kafka error in receive_chat_message: {e}")
        time.sleep(4)
