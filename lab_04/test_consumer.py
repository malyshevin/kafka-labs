from confluent_kafka import Consumer

# Конфигурация Kafka Consumer
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'python-consumer',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
# topic = 'postgres.public.users'
topic = 'postgres.public.orders'

consumer.subscribe([topic])

print(f"Listening to topic: {topic}")
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            print("\n\nConsumer error: {}".format(msg.error()))
            continue
        print(f"\n\nReceived message: {msg.value().decode('utf-8')}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
