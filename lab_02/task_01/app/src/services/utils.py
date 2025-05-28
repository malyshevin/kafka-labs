import os
import sys
import logging


logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_env(name, default):
    return os.environ.get(name, default)


def wrap_delivery_report(logger):
    def delivery_report(err, msg):
        if err is not None:
            logger.warning(f"🚫 Message delivery failed: {err}")
            return

        logger.info(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")

    return delivery_report


def get_new_user_id(tmp_file):
    if not os.path.exists(tmp_file):
        with open(tmp_file, "w") as f:
            f.write("1")
        return 1

    with open(tmp_file, "r+") as f:
        cur = int(f.read())
        f.seek(0)
        f.write(str(cur + 1))
        f.truncate()
        return cur + 1
