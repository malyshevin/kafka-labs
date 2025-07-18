import os
import faust
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

PRODUCTS_TOPIC = "products"
FILTERED_PRODUCTS_TOPIC = "filtered_products"
REQUESTS_TO_BLOCK_PRODUCTS_TOPIC = "requests_to_block_products"


class AvroSchema:
    def __init__(self, topic):
        self.schema_registry_conf = {"url": os.getenv("SCHEMA_REGISTRY_URL")}
        self.schema_registry_client = SchemaRegistryClient(self.schema_registry_conf)

        self.schema_str = self.schema_registry_client.get_latest_version(topic).schema.schema_str

        self.avro_serializer = AvroSerializer(
            schema_registry_client=self.schema_registry_client,
            schema_str=self.schema_str
        )

        self.avro_deserializer = AvroDeserializer(
            schema_registry_client=self.schema_registry_client,
            schema_str=self.schema_str
        )

        self.context = SerializationContext(topic, MessageField.VALUE)

    def serialize(self, data):
        return self.avro_serializer(data, self.context)

    def deserialize(self, data):
        return self.avro_deserializer(data, self.context)


class BlockRequest(faust.Record, serializer="json"):
    action: str
    product_id: str
