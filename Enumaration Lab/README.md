# ImranTheExploitHunter — OSCP-Style Enumeration PentestLab

Local, original training lab built from the supplied learning material. It covers DNS, Nmap/port scanning, SMB, SMTP, SNMP, and Windows built-in enumeration concepts.

> **Authorized training only.** Use against this lab or systems you are explicitly authorized to assess.

## Quick start — Kali + Podman/Docker

```bash
unzip ithlab-enumeration-oscp-style-final.zip
cd final-lab
chmod +x start.sh stop.sh reset.sh
./start.sh
```

Open `http://127.0.0.1:8080`.

Lab addresses:

- Target: `172.31.77.10`
- DNS: `172.31.77.2`
- Domain: `oscp.local`
- TCP: `22,25,80,139,445`
- UDP: `161`
- DNS: `53/tcp,53/udp`

## DNS resolver note

The lab DNS is intentionally isolated. Use the DNS server explicitly:

```bash
host oscp.local 172.31.77.2
host -t MX oscp.local 172.31.77.2
host -t TXT oscp.local 172.31.77.2
```

Do not overwrite Kali's normal `/etc/resolv.conf` just for this lab.

## Learning coverage

### DNS
- A/MX/TXT/NS records
- Forward lookup
- Invalid-hostname/NXDOMAIN testing
- Reverse/PTR discovery
- Bash DNS brute forcing
- DNSRecon standard enumeration
- DNSRecon brute force
- DNSEnum
- Windows `nslookup` concept

### Nmap
- Default TCP scanning
- Full TCP scanning
- SYN/stealth scanning
- TCP Connect scanning
- UDP scanning
- TCP+UDP discovery
- Network sweeping / `-sn`
- Greppable output / `-oG`
- Top-port sweeps
- OS fingerprinting / `-O`
- Service detection / `-sV`
- NSE / `http-headers`
- Scan-footprint awareness

### SMB
- 139/445 discovery
- NetBIOS names
- `nbtscan`
- SMB metadata
- `enum4linux-ng`
- Anonymous share discovery
- `smbclient`
- SMB NSE / `smb-os-discovery`
- Windows `net view` concept

### SMTP
- TCP/25
- Banner enumeration
- `VRFY`
- `EXPN`
- Manual interaction with `nc`
- Python socket automation concept
- Windows `Test-NetConnection` / Telnet concept

### SNMP
- UDP/161
- Community strings
- `onesixtyone`
- MIB/OID concepts
- `snmpwalk`
- System information
- Process enumeration
- Installed software context
- Listening-port enumeration
- Host-level information vs external scanning

### Windows
- `Test-NetConnection`
- `TcpTestSucceeded`
- PowerShell `foreach` port loop
- Living-off-the-land enumeration concept

## Walkthrough password

`ITEH`

## Stop / reset

```bash
./stop.sh
./reset.sh
```

Reset removes the lab runtime and clears challenge submissions before provisioning a fresh lab.
