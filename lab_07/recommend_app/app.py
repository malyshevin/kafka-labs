import os
import uuid
from confluent_kafka import Consumer
from hdfs import InsecureClient


consumer_conf = {
    "bootstrap.servers": os.getenv(f"ANALYTICS_KAFKA_BOOTSTRAP_SERVERS"),
    "security.protocol": "SSL",

    "ssl.keystore.location": f"/app/ssl/hdfs/hdfs.keystore.p12",
    "ssl.keystore.password": os.getenv("SSL_KEYSTORE_PASSWORD"),

    "ssl.ca.location": "/app/ssl/ca.crt",
    "ssl.certificate.location": f"/app/ssl/hdfs/hdfs.crt",

    "ssl.key.location": f"/app/ssl/hdfs/hdfs.key",
    "ssl.key.password": os.getenv("SSL_KEY_PASSWORD"),

    "ssl.endpoint.identification.algorithm": "none",

    "group.id": "hadoop-consumer-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
    "session.timeout.ms": 10_000,
}


if __name__ == "__main__":
   consumer = Consumer(consumer_conf)
   consumer.subscribe(["product_requests", "recommendation_requests"])

   hdfs_client = InsecureClient("http://localhost:9870", user="root")

   try:
       while True:
           msg = consumer.poll(0.1)

           if msg is None:
               continue
           if msg.error():
               print(f"Ошибка: {msg.error()}")
               continue

           value = msg.value().decode("utf-8")
           print(
               f"Получено сообщение: {value=}, "
               f"partition={msg.partition()}, offset={msg.offset()}"
           )

           hdfs_file = f"data/message_{uuid.uuid4()}"

           with hdfs_client.write(hdfs_file, encoding="utf-8") as writer:
               writer.write(value + "\n")

           print(f"Сообщение '{value=}' записано в HDFS по пути '{hdfs_file}'")

           with hdfs_client.read(hdfs_file, encoding="utf-8") as reader:
               content = reader.read()
    
           print(f"Чтение файла '{hdfs_file}' из HDFS. Содержимое файла: '{content.strip()}'")
   finally:
       print("close consumer")
       consumer.close()
