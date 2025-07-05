#!/bin/bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
cd /opt/nifi

# Остановить если запущен
./bin/nifi.sh stop
sleep 5

# Запустить в фоне
nohup ./bin/nifi.sh run > /tmp/nifi.out 2>&1 &
echo $! > /tmp/nifi.pid

echo "NiFi starting... Check logs:"
echo "tail -f /opt/nifi/logs/nifi-app.log"
echo "tail -f /tmp/nifi.out"