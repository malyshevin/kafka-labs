import os
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

PRODUCTS_TOPIC = "products"
PRODUCT_REQUESTS_TOPIC = "product_requests"
RECOMMENDATIONS_REQUESTS_TOPIC = "recommendation_requests"

REQUESTS_TO_BLOCK_PRODUCTS_TOPIC = "requests_to_block_products"


def get_kafka_config(api_name, cluster_type="PROD"):
    assert cluster_type in ("PROD", "ANALYTICS")

    return {
        "bootstrap.servers": os.getenv(f"{cluster_type}_KAFKA_BOOTSTRAP_SERVERS"),
        "security.protocol": "SSL",

        "ssl.keystore.location": f"/app/ssl/{api_name}/{api_name}.keystore.p12",
        "ssl.keystore.password": os.getenv("SSL_KEYSTORE_PASSWORD"),

        "ssl.ca.location": "/app/ssl/ca.crt",
        "ssl.certificate.location": f"/app/ssl/{api_name}/{api_name}.crt",

        "ssl.key.location": f"/app/ssl/{api_name}/{api_name}.key",
        "ssl.key.password": os.getenv("SSL_KEY_PASSWORD"),

        "ssl.endpoint.identification.algorithm": "none"
    }


def get_schema_registry_url():
    return os.getenv("SCHEMA_REGISTRY_URL")


def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Ошибка доставки: {err}")
    else:
        print(f"✅ Сообщение доставлено в {msg.topic()} [{msg.partition()}]")


def send_to_kafka(api_name, cluser, topic, data, data_to_dict_func, key):
    schema_registry_conf = {"url": get_schema_registry_url()}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    schema_str = schema_registry_client.get_latest_version(topic).schema.schema_str

    avro_serializer = AvroSerializer(
        schema_registry_client=schema_registry_client,
        schema_str=schema_str,
        to_dict=data_to_dict_func
    )

    producer = Producer(get_kafka_config(api_name, cluser))
    print(f"Список топиков в кластере {producer.list_topics(timeout=10)}")  # Проверка подключения к кластеру

    producer.produce(
        topic=topic,
        value=avro_serializer(data, SerializationContext(topic, MessageField.VALUE)),
        key=str(key).encode("utf-8"),
        callback=delivery_report
    )

    print(f"Сообщений в очереди: {len(producer)}")
    print(f"Ошибки: {producer.flush(timeout=20)}")

    print(f"✅ Продукт отправлен в Kafka (key: key)")
