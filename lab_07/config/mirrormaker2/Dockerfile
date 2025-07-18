FROM confluentinc/cp-kafka:7.4.0

COPY connect-log4j.properties /etc/kafka/connect-log4j.properties
ENV KAFKA_LOG4J_OPTS="-Dlog4j.configuration=file:/etc/kafka/connect-log4j.properties"
