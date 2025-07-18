import re
import json
import uuid
import argparse
from datetime import datetime
from common import (
    PRODUCT_REQUESTS_TOPIC,
    RECOMMENDATIONS_REQUESTS_TOPIC,
    send_to_kafka,
)

API_NAME = "client_api"
CLUSTER = "ANALYTICS"


class ProductRequest:
    def __init__(self, **kwargs):
        self.request_id = kwargs.get("request_id", str(uuid.uuid4()))
        self.product_id = kwargs.get("product_id")
        self.timestamp = kwargs.get("timestamp", datetime.now().isoformat())
        self.api_name = API_NAME
        self.request_type = "product_info"


class RecommendationRequest:
    def __init__(self, **kwargs):
        self.request_id = kwargs.get("request_id", str(uuid.uuid4()))
        self.product_id = kwargs.get("product_id")  # Optional, может быть None для общих рекомендаций
        self.timestamp = kwargs.get("timestamp", datetime.now().isoformat())
        self.api_name = API_NAME
        self.request_type = "recommendations"
        self.limit = kwargs.get("limit", 5)  # Количество рекомендаций по умолчанию


def product_request_to_dict(request: ProductRequest, ctx):
    return {
        "request_id": request.request_id,
        "product_id": request.product_id,
        "timestamp": request.timestamp,
        "api_name": request.api_name,
        "request_type": request.request_type
    }


def recommendation_request_to_dict(request: RecommendationRequest, ctx):
    return {
        "request_id": request.request_id,
        "product_id": request.product_id,
        "timestamp": request.timestamp,
        "api_name": request.api_name,
        "request_type": request.request_type,
        "limit": request.limit
    }


def parse_struct_line(line):
    """Преобразует строку вида 'Struct{...}' в словарь Python."""
    if not line.startswith("Struct{") or not line.endswith("}"):
        raise ValueError("Неверный формат строки (должно быть Struct{...})")

    # Удаляем "Struct{" и закрывающую "}"
    content = line[len("Struct{"):-1]

    # Разбиваем на пары ключ=значение, учитывая вложенные Struct и списки
    parsed_dict = {}
    current_key = None
    current_value = []
    depth = 0  # Глубина вложенности (для Struct, списков, словарей)

    for token in re.split(r'([,=])', content):
        token = token.strip()
        if not token:
            continue

        if token == '=' and depth == 0:
            current_key = current_value.pop() if current_value else None
            current_value = []
        elif token == ',' and depth == 0:
            if current_key and current_value:
                parsed_dict[current_key] = ''.join(current_value).strip()
                current_key = None
                current_value = []
        else:
            if token in ('{', '['):
                depth += 1
            elif token in ('}', ']'):
                depth -= 1
            current_value.append(token)

    if current_key and current_value:
        parsed_dict[current_key] = ''.join(current_value).strip()

    # Постобработка значений (преобразование чисел, списков и вложенных Struct)
    for key, value in parsed_dict.items():
        if value.startswith("Struct{"):
            parsed_dict[key] = parse_struct_line(value)
        elif value.startswith("[") and value.endswith("]"):
            # Обработка списков (простейший вариант)
            items = value[1:-1].split(",")
            parsed_dict[key] = [item.strip() for item in items if item.strip()]
        elif value == "None":
            parsed_dict[key] = None
        elif value.isdigit():
            parsed_dict[key] = int(value)
        elif re.match(r'^\d+\.\d+$', value):
            parsed_dict[key] = float(value)
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            parsed_dict[key] = datetime.strptime(value, "%Y-%m-%d").date()

    return parsed_dict


def find_product_by_id(product_id, file_path):
    last_match = None

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            product = parse_struct_line(line)

            if str(product.get("product_id")) == str(product_id):
                last_match = product

    return last_match


def get_product_info(product_id):
    product_id = product_id if product_id else str(uuid.uuid4())
    request = ProductRequest(product_id=product_id)

    send_to_kafka(API_NAME, CLUSTER, PRODUCT_REQUESTS_TOPIC, request, product_request_to_dict, product_id)

    product_info = find_product_by_id(product_id, './kafka-connect/filtered_products.txt')
    return product_info if product_info is not None else {}


def get_recommendations(product_id, limit=5):
    product_id = product_id if product_id else str(uuid.uuid4())
    request = RecommendationRequest(product_id=product_id, limit=limit)

    send_to_kafka(
        API_NAME,
        CLUSTER,
        RECOMMENDATIONS_REQUESTS_TOPIC,
        request,
        recommendation_request_to_dict,
        product_id
    )

    recommendations = []
    for i in range(1, limit + 1):
        recommendations.append({
            "product_id": f"rec_{i}_{product_id or 'general'}",
            "name": f"Рекомендованный продукт {i}",
            "price": {"amount": 100.0 * i, "currency": "RUB"},
            "score": 0.9 - (i * 0.1)
        })

    return recommendations


def parse_args():
    parser = argparse.ArgumentParser(
        description="Клиентский API для работы с продуктами и рекомендациями",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Доступные команды')

    # Парсер для получения информации о продукте
    product_parser = subparsers.add_parser('product', help='Получить информацию о продукте')
    product_parser.add_argument('--id', required=True, help='ID продукта')
    product_parser.add_argument('--output', choices=['json', 'pretty'], default='pretty',
                              help='Формат вывода результатов')

    # Парсер для получения рекомендаций
    rec_parser = subparsers.add_parser('recommend', help='Получить рекомендации')
    rec_parser.add_argument('--id', help='ID продукта для персонализированных рекомендаций')
    rec_parser.add_argument('--limit', type=int, default=5,
                          help='Количество возвращаемых рекомендаций')
    rec_parser.add_argument('--output', choices=['json', 'pretty'], default='pretty',
                          help='Формат вывода результатов')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'product':
        result = get_product_info(args.id)
    elif args.command == 'recommend':
        result = get_recommendations(product_id=args.id, limit=args.limit)
    else:
        raise ValueError(f"Неизвестная команда: {args.command}")

    print("Результат запроса:")
    print(result)

    # if args.output == 'json':
    #     print(json.dumps(result, ensure_ascii=False))
    # else:
    #     print("Результат запроса:")
    #     print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
