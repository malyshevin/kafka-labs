rm -rf tmp_data

mkdir -p tmp_data
cd tmp_data

mkdir -p prod-zookeeper-data analytics-zookeeper-data
mkdir -p prod-zookeeper-log analytics-zookeeper-log

chmod -R 777 prod-zookeeper-data analytics-zookeeper-data
chmod -R 777 prod-zookeeper-log analytics-zookeeper-log

mkdir -p kafka-connect
chmod -R 777 kafka-connect

cd ..
