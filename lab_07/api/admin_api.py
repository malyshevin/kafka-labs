import uuid
import json
import argparse
from confluent_kafka import Producer
from common import (
    REQUESTS_TO_BLOCK_PRODUCTS_TOPIC,
    get_kafka_config,
    delivery_report,
)

API_NAME = "admin_api"
CLUSTER = "PROD"


def send_ban_request(action, product_id):
    producer = Producer(get_kafka_config(API_NAME, CLUSTER))

    product_id = product_id if product_id else str(uuid.uuid4())

    request = {
        "action": action,
        "product_id": product_id
    }

    producer.produce(
        topic=REQUESTS_TO_BLOCK_PRODUCTS_TOPIC,
        key=str(product_id).encode("utf-8"),
        value=json.dumps(request).encode("utf-8"),
        callback=delivery_report
    )

    print(f"Сообщений в очереди: {len(producer)}")
    print(f"Ошибки: {producer.flush(timeout=5)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="API для управления функциями администратора")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--add', help='Добавить ID в список забаненых продуктов')
    group.add_argument('--remove', help='Удалить ID из списка забаненых продуктов')

    args = parser.parse_args()

    if args.add:
        send_ban_request("add", args.add)
        print(f"✅ Запрос на добавление выполнен")

    if args.remove:
        send_ban_request("remove", args.remove)
        print(f"✅ Запрос на удаление выполнен")
