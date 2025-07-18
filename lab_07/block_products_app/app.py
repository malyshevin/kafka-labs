import os
import sys
import ssl
import faust
import logging
from utils import (
    PRODUCTS_TOPIC,
    FILTERED_PRODUCTS_TOPIC,
    REQUESTS_TO_BLOCK_PRODUCTS_TOPIC,
    AvroSchema,
    BlockRequest,
)

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APP_NAME = "block_products_app"


#### Настройка SSL подключения ####
ssl_context = ssl.create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH,
    cafile="/app/ssl/ca.crt"
)
ssl_context.load_cert_chain(
    f"/app/ssl/{APP_NAME}/{APP_NAME}.crt",
    keyfile=f"/app/ssl/{APP_NAME}/{APP_NAME}.key",
    password=os.getenv("SSL_KEY_PASSWORD")
)

#### Настройка приложения
app = faust.App(
    APP_NAME,
    broker=os.getenv("PROD_KAFKA_BOOTSTRAP_SERVERS"),
    broker_credentials=ssl_context,
    store="rocksdb://",
)


#### Топики ####
products = app.topic(PRODUCTS_TOPIC, value_serializer='raw')
filtered_products = app.topic(FILTERED_PRODUCTS_TOPIC, value_serializer='raw')
requests_to_block_products = app.topic(REQUESTS_TO_BLOCK_PRODUCTS_TOPIC, value_type=BlockRequest)

#### Таблицы ####
block_ids_table = app.Table("block_ids", default=lambda: list(), partitions=3)


#### Агент для обработки запросов на удаление / добавление заблокированных ID продуктов ####
@app.agent(requests_to_block_products)
async def update_block_ids(commands):
    async for cmd in commands:
        logger.info(f"-> [Update block ids] Start process msg {cmd}")
        ids = set(block_ids_table["ids"])

        if cmd.action == "add":
            ids.add(cmd.product_id)

        if cmd.action == "remove":
            ids.discard(cmd.product_id)

        block_ids_table["ids"] = list(ids)
        logger.info(f"🟩 [Update block ids] New blocked ids {block_ids_table['ids']}")


# работа со Schema Registry для корректной обработки сообщений типа Product
avro_product = AvroSchema(PRODUCTS_TOPIC)
avro_filtered_product = AvroSchema(FILTERED_PRODUCTS_TOPIC)


#### Агент для фильтрации продуктов из топика products в топик  filtered_products ####
@app.agent(products)
async def process_products(stream):
    async for product_bytes in stream:
        logging.info(f"Received msg from topic 'products'")

        product = avro_product.deserialize(product_bytes)
        product_id = product["product_id"]

        logging.info(f"Product id: {product_id}")

        blocked_ids = block_ids_table["ids"]
        logging.info(f"{blocked_ids}")

        if product["product_id"] in blocked_ids:
            logging.info(f"🚫 Product with ID {product_id} was blocked (list of blocked ids {blocked_ids})")
        else:
            filtered_product_bytes = avro_filtered_product.serialize(product)
            await filtered_products.send(value=filtered_product_bytes, key=str(product_id).encode("utf-8"))

            logging.info(f"🟩 Sent to filtered_products: {product_id}")

        logging.info(f"Agent process_products wait next msg")


if __name__ == "__main__":
    app.main()
