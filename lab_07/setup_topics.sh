prod_container="lab_07_v2-prod-broker1-1"
analytics_container="lab_07_v2-analytics-broker1-1"

prod_server="prod-broker1:9092"
analytics_server="analytics-broker1:9092"

ssl_properties="/etc/kafka/secrets/client-ssl.properties"

#### PROD CLUSTER ####

docker exec -it "$prod_container" kafka-topics --create \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --topic products \
  --partitions 3 \
  --replication-factor 3

docker exec -it "$prod_container" kafka-topics --create \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --topic filtered_products \
  --partitions 3 \
  --replication-factor 3

docker exec -it "$prod_container" kafka-topics --create \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --topic requests_to_block_products \
  --partitions 3 \
  --replication-factor 3

#### ANALYTICS CLUSTER ####

docker exec -it "$analytics_container" kafka-topics --create \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --topic product_requests \
  --partitions 3 \
  --replication-factor 3

docker exec -it "$analytics_container" kafka-topics --create \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --topic recommendation_requests \
  --partitions 3 \
  --replication-factor 3
