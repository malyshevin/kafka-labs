from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import time
import ssl

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

producer_conf = {
    'bootstrap.servers': 'rc1a-1dtppv0ei700ror4.mdb.yandexcloud.net:9091,rc1b-qcf9i2q5todkaqo7.mdb.yandexcloud.net:9091,rc1d-65ks63ccs7naqnmp.mdb.yandexcloud.net:9091',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'SCRAM-SHA-512',
    'sasl.username': 'kafka-user',
    'sasl.password': '123P!',
    'ssl.ca.location': 'YandexCA.crt'
}

schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_serializer = AvroSerializer(schema_registry_client, schema_str)
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

for i in range(10):
    user = {
        'id': i,
        'name': f'User {i}',
        'email': f'user{i}@example.com',
        'created_at': int(time.time() * 1000)
    }
    
    print(f'Producing message: {user}')
    
    producer.produce(
        topic='production-topic',
        key=str(i),
        value=avro_serializer(user, SerializationContext('production-topic', MessageField.VALUE)),
        on_delivery=delivery_report
    )
    
    producer.poll(0)
    time.sleep(1)

producer.flush()
print('All messages sent!')
