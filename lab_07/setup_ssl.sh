
rm -rf ssl
mkdir -p ssl
cd ssl

echo -e "⏳ Создание CA (Certificate Authority)"

mkdir -p ca
cd ca

openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -days 3650 -subj "/CN=MyKafkaCA"

cd ..
echo -e "✅ CA созданы успешно\n"

echo -e "⏳ Создание ключей для брокеров\n"

for cluster in "prod" "analytics"; do
  for i in 1 2 3; do
    broker="${cluster}-broker${i}"
    echo "⏳ Создание ключей для $broker"

    mkdir -p $broker
    cd $broker

    openssl genrsa -out $broker.key 2048
    openssl req -new -key $broker.key -out $broker.csr -subj "/CN=$broker"

    cd ..

    openssl x509 -req -in $broker/$broker.csr -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial -out $broker/$broker.crt -days 365 -sha256

    openssl pkcs12 -export \
        -in $broker/$broker.crt \
        -inkey $broker/$broker.key \
        -chain -CAfile ca/ca.crt \
        -name $broker \
        -out $broker/$broker.keystore.p12 \
        -password pass:changeit

    keytool -import -noprompt \
        -alias ca \
        -file ca/ca.crt \
        -keystore $broker/$broker.truststore.p12 \
        -storetype PKCS12 \
        -storepass changeit

    cat > $broker/client-ssl.properties << EOF
    security.protocol=SSL
    ssl.truststore.location=/etc/kafka/secrets/$broker.truststore.p12
    ssl.truststore.password=changeit
    ssl.truststore.type=PKCS12
    ssl.keystore.location=/etc/kafka/secrets/$broker.keystore.p12
    ssl.keystore.password=changeit
    ssl.keystore.type=PKCS12
    ssl.key.password=changeit
EOF

    echo "changeit" > $broker/${broker}_keystore_creds
    echo "changeit" > $broker/${broker}_truststore_creds
    echo "changeit" > $broker/${broker}_key_creds

    openssl x509 -in $broker/$broker.crt -text -noout | grep Subject:

    echo -e "✅ Ключи для $broker созданы\n"
  done
done

echo -e "⏳ Создание ключей для сторонних сервисов\n"

for service in "kafka-ui" "mirrormaker2" "schema-registry" "shop_api" "client_api" "admin_api" "block_products_app" "kafka-exporter" "kafka-connect" "hdfs"; do
    echo -e "⏳ Создание ключей для $service"

    mkdir -p $service
    cd $service

    openssl genrsa -out $service.key 2048
    openssl req -new -key $service.key -out $service.csr -subj "/CN=$service"

    cd ..

    openssl x509 -req -in $service/$service.csr -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial -out $service/$service.crt -days 365 -sha256

    openssl pkcs12 -export \
        -in $service/$service.crt \
        -inkey $service/$service.key \
        -chain -CAfile ca/ca.crt \
        -name $service \
        -out $service/$service.keystore.p12 \
        -password pass:changeit

    keytool -import -noprompt \
        -alias ca \
        -file ca/ca.crt \
        -keystore $service/$service.truststore.p12 \
        -storetype PKCS12 \
        -storepass changeit

    if [ "$service" == "schema-registry" ]; then
        etc_dir="schema-registry"
    else
        etc_dir="kafka"
    fi

        cat > $service/client-ssl.properties << EOF
    security.protocol=SSL
    ssl.truststore.location=/etc/$etc_dir/secrets/$service.truststore.p12
    ssl.truststore.password=changeit
    ssl.truststore.type=PKCS12
    ssl.keystore.location=/etc/$etc_dir/secrets/$service.keystore.p12
    ssl.keystore.password=changeit
    ssl.keystore.type=PKCS12
    ssl.key.password=changeit
EOF

    echo "changeit" > $service/${service}_keystore_creds
    echo "changeit" > $service/${service}_truststore_creds
    echo "changeit" > $service/${service}_key_creds

    openssl x509 -in $service/$service.crt -text -noout | grep Subject:

    echo -e "✅ Ключи для $service созданы\n"
done
