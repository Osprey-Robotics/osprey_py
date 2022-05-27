#!/bin/bash
echo "Checking if the usual router IP is reachable (192.168.1.1)"
if timeout 1 nc -vz 192.168.1.1 80; then echo "It is"; else echo "It isn't"; fi
routerIP=$(ip route show | grep -i 'default via'| awk '{print $3 }'|tr -d '\n')
echo "Router IP is ${routerIP}"
echo "Looking for Joule IP address:"
curl -s -u "admin:ospreyrobotics" "http://${routerIP}/DHCPTable.asp"|grep 'ospreyrobotics'|cut -d "'" -f4
