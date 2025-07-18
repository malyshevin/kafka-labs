prod_container="lab_07_v2-prod-broker1-1"
analytics_container="lab_07_v2-analytics-broker1-1"

prod_server="prod-broker1:9092"
analytics_server="analytics-broker1:9092"

ssl_properties="/etc/kafka/secrets/client-ssl.properties"

mirrormaker_user="User:CN=mirrormaker2"
shop_api_user="User:CN=shop_api"
client_api_user="User:CN=client_api"
admin_api_user="User:CN=admin_api"
block_app_user="User:CN=block_products_app"
kafka_exporter="User:CN=kafka-exporter"
kafka_connect="User:CN=kafka-connect"

#### SHOP API ####

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$shop_api_user" \
  --operation Write \
  --topic 'products'

#### CLIENT API ####

docker exec -it "$analytics_container" kafka-acls \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$client_api_user" \
  --operation Write \
  --topic 'product_requests'

docker exec -it "$analytics_container" kafka-acls \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$client_api_user" \
  --operation Write \
  --topic 'recommendation_requests'

#### ADMIN API ####

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$admin_api_user" \
  --operation Write \
  --topic 'requests_to_block_products'

### BLOCK PRODUCTS APP ####

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$block_app_user" \
  --operation Read \
  --topic 'requests_to_block_products'

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$block_app_user" \
  --operation Read \
  --topic 'products'

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$block_app_user" \
  --operation Write \
  --topic 'filtered_products'

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$block_app_user" \
  --operation All \
  --topic "*"

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$block_app_user" \
  --operation All --group '*'

#### Mirror Maker ####

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$mirrormaker_user" \
  --operation Read --operation Describe \
  --topic '*' --group '*'

docker exec -it "$analytics_container" kafka-acls \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$mirrormaker_user" \
  --operation Write --operation Create --operation Describe \
  --topic '*'

docker exec -it "$analytics_container" kafka-acls \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$mirrormaker_user" \
  --operation All --group '*'

#### Kafka Exporter ####

docker exec -it "$analytics_container" kafka-acls \
  --bootstrap-server "$analytics_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$kafka_exporter" \
  --operation Read --operation Describe \
  --topic '*' --group '*'

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$kafka_exporter" \
  --operation Read --operation Describe \
  --topic '*' --group '*'

#### Kafka Connect ####

docker exec -it "$prod_container" kafka-acls \
  --bootstrap-server "$prod_server" \
  --command-config "$ssl_properties" \
  --add --allow-principal "$kafka_connect" \
  --operation All \
  --topic '*' --group '*'
