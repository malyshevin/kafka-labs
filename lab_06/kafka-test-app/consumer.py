from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
import sys

schema_registry_conf = {
    'url': 'http://89.169.157.15:8081'
}

schema_str = """
{
  "type": "record",
  "name": "User",
  "namespace": "com.example",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"},
    {"name": "email", "type": "string"},
    {"name": "created_at", "type": "long", "logicalType": "timestamp-millis"}
  ]
}
"""

consumer_conf = {
    'bootstrap.servers': 'rc1a-1dtppv0ei700ror4.mdb.yandexcloud.net:9091,rc1b-qcf9i2q5todkaqo7.mdb.yandexcloud.net:9091,rc1d-65ks63ccs7naqnmp.mdb.yandexcloud.net:9091',
    'group.id': 'test-consumer-group',
    'auto.offset.reset': 'earliest',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'SCRAM-SHA-512',
    'sasl.username': 'kafka-user',
    'sasl.password': '123P!',
    'ssl.ca.location': 'YandexCA.crt'
}

schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_deserializer = AvroDeserializer(schema_registry_client, schema_str)
consumer = Consumer(consumer_conf)

consumer.subscribe(['production-topic'])

print('Starting consumer... Press Ctrl+C to exit')

try:
    while True:
        msg = consumer.poll(1.0)
        
        if msg is None:
            continue
            
        if msg.error():
            print(f'Consumer error: {msg.error()}')
            continue

        user = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
        
        print(f'Received message:')
        print(f'  Key: {msg.key().decode("utf-8")}')
        print(f'  Value: {user}')
        print(f'  Partition: {msg.partition()}')
        print(f'  Offset: {msg.offset()}')
        print(f'  Timestamp: {msg.timestamp()}')
        print('-' * 50)
        
except KeyboardInterrupt:
    print('Interrupted by user')
finally:
    consumer.close()
    print('Consumer closed')
