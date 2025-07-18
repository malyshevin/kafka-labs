import argparse
import json
import uuid
from datetime import datetime
from common import (
    PRODUCTS_TOPIC,
    send_to_kafka,
)

API_NAME = "shop_api"
CLUSTER = "PROD"


class Product:
    def __init__(self, **kwargs):
        self.product_id = kwargs.get("product_id", str(uuid.uuid4()))
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.price = kwargs.get("price", {"amount": 0.0, "currency": "RUB"})
        self.category = kwargs.get("category", "Другое")
        self.brand = kwargs.get("brand", "")
        self.stock = kwargs.get("stock", {"available": 0, "reserved": 0})
        self.sku = kwargs.get("sku")
        self.tags = kwargs.get("tags", [])
        self.images = kwargs.get("images", [])
        self.specifications = kwargs.get("specifications", {})
        now = datetime.now().strftime("%Y-%m-%d")
        self.created_at = kwargs.get("created_at", now)
        self.updated_at = kwargs.get("updated_at", now)
        self.index = kwargs.get("index", "products")
        self.store_id = kwargs.get("store_id", "store_001")


def product_to_dict(product, ctx):
    return {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "brand": product.brand,
        "stock": product.stock,
        "sku": product.sku,
        "tags": product.tags,
        "images": product.images,
        "specifications": product.specifications,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "index": product.index,
        "store_id": product.store_id
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Добавление товара в магазин")

    parser.add_argument("--id", help="ID товара")
    parser.add_argument("--name", help="Название товара")
    parser.add_argument("--price", help="Цена товара")
    parser.add_argument("--description", help="Описание товара")
    parser.add_argument("--category", help="Категория товара")
    parser.add_argument("--brand", help="Бренд товара")

    # JSON-файл как альтернатива
    parser.add_argument("--json_file", help="Путь к JSON-файлу с полным описанием товара")

    args = parser.parse_args()
    
    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as f:
            products = json.load(f)
            return [Product(**p) for p in products]
        
    coalesce = lambda v, tmp: v if v is not None else tmp

    return [
        Product(
            product_id=coalesce(str(args.id), str(uuid.uuid4())),
            name=coalesce(args.name, ''),
            price={"amount": coalesce(args.price, 0.0), "currency": "RUB"},
            description=coalesce(args.description, ''),
            category=coalesce(args.category, ''),
            brand=coalesce(args.brand, '')
        )
    ]


if __name__ == "__main__":
    products = parse_args()

    for product in products:
        send_to_kafka(API_NAME, CLUSTER, PRODUCTS_TOPIC, product, product_to_dict, product.product_id)
