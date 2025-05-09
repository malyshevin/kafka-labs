import os
import sys
import json
import logging


def get_logger(name):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(name)


def get_env(name, default):
    return os.environ.get(name, default)


class CustomMessage:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def to_json(self, logger):
        try:
            message_json = json.dumps({'key': self.key, 'value': self.value})
            logger.info(f"Serialized Message: {message_json}")
            return message_json

        except TypeError as e:
            logger.error(f"Serialization error: {e}")
            return None

    @staticmethod
    def from_json(json_str, logger):
        try:
            data = json.loads(json_str)
            logger.info(f"Deserialized Message: {data}")
            return CustomMessage(key=data.get('key'), value=data.get('value'))

        except json.JSONDecodeError as e:
            logger.error(f"Deserialization error: {e}")
            return None
