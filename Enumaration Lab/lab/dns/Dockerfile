FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends bind9 bind9-utils ca-certificates && rm -rf /var/lib/apt/lists/*
COPY named.conf /etc/bind/named.conf
COPY db.oscp.local /etc/bind/db.oscp.local
COPY db.172.31.77 /etc/bind/db.172.31.77
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 53/tcp 53/udp
ENTRYPOINT ["/entrypoint.sh"]
