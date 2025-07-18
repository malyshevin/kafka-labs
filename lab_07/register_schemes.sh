#!/bin/bash

echo -e "⏳ Регистрация схем из config/schema_registry "

for schema in "products" "product_requests" "recommendation_requests" "filtered_products"; do
  schema_file=config/schema_registry/$schema.avsc
  schema_json=$(cat "$schema_file" | jq -c . | jq -Rs .)

  data=$(echo "{\"schema\": $schema_json}")

  curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    --data "$data" \
    http://localhost:8081/subjects/${schema}/versions

  echo -e "✅ Схема $schema успешно зарегистрирована"
done
