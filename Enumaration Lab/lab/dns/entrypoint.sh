#!/bin/sh
set -eu
sed -i "s/TARGET_IP/${TARGET_IP:-172.31.77.10}/g; s/DNS_IP/${DNS_IP:-172.31.77.2}/g" /etc/bind/db.oscp.local
mkdir -p /run/named
chown bind:bind /run/named || true
exec /usr/sbin/named -g -c /etc/bind/named.conf -u bind
