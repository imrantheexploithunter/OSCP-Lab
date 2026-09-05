FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends nginx openssh-server samba samba-common-bin postfix python3 snmpd supervisor ca-certificates iproute2 procps net-tools && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash labuser && echo 'labuser:LabPass123!' | chpasswd
RUN mkdir -p /var/run/sshd /srv/Public && printf '%s\n' 'ImranTheExploitHunter OSCP-Style Training Share' 'FLAG{SMB_PUBLIC_SHARE}' > /srv/Public/readme.txt
COPY smb.conf /etc/samba/smb.conf
COPY snmpd.conf /etc/snmp/snmpd.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY nginx.conf /etc/nginx/sites-available/default
COPY postfix-main.cf /etc/postfix/main.cf
COPY smtp_server.py /opt/iteh/smtp_server.py
RUN printf '%s\n' 'ImranTheExploitHunter | OSCP-Style Practice Target' > /var/www/html/index.html
EXPOSE 22 25 80 139 445 161/udp
CMD ["/usr/bin/supervisord","-n"]
