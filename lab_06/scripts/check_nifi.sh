#!/bin/bash
echo "=== NiFi Status ==="
sudo systemctl status nifi --no-pager | head -10
echo -e "\n=== Port 8080 ==="
sudo ss -tlnp | grep 8080 || echo "Port 8080 not listening"
echo -e "\n=== Last logs ==="
tail -5 /opt/nifi/logs/nifi-app.log 2>/dev/null || echo "No app log"
echo -e "\n=== Memory ==="
free -h | grep Mem