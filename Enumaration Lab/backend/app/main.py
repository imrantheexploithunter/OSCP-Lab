import os, sqlite3
from pathlib import Path
import docker
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

NAME='ImranTheExploitHunter | OSCP-Style PentestLab'
DATA=Path(os.getenv('DATA_DIR','/data')); DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'lab.db'
NETWORK='ith-oscp-lab'
SUBNET=os.getenv('LAB_SUBNET','172.31.77.0/24')
TARGET='172.31.77.10'; DNS='172.31.77.2'
TARGET_IMAGE=os.getenv('TARGET_IMAGE','imrantheexploithunter-target:5.0')
DNS_IMAGE=os.getenv('DNS_IMAGE','imrantheexploithunter-dns:5.0')

app=FastAPI(title=NAME,version='5.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])

MODULES={
'nmap':[
 {'id':'nmap-01','title':'Find the live target with a host sweep','answer':'172.31.77.10','points':50,'hint':'Use Nmap host discovery across the lab subnet and save greppable output.','walkthrough':"""1. Sweep the lab range:\n\n   nmap -v -sn 172.31.77.1-253 -oG ping-sweep.txt\n\n2. Extract live hosts:\n\n   grep Up ping-sweep.txt | cut -d \" \" -f 2\n\n3. Identify the target address.\n4. Submit the live target IP."""},
 {'id':'nmap-02','title':'Identify the SMB TCP port','answer':'445','points':50,'hint':'Scan the target for all TCP ports.','walkthrough':"""1. Run a full TCP scan:\n\n   nmap -p- -Pn 172.31.77.10\n\n2. Locate the SMB service.\n3. Submit its TCP port number."""},
 {'id':'nmap-03','title':'Identify the web server with service detection','answer':'1.22.1','points':50,'hint':'Use service version detection on TCP/80.','walkthrough':"""1. Run:\n\n   nmap -sC -sV -p80 172.31.77.10\n\n2. Read the SERVICE VERSION result.\n3. Submit the web Service Version"""},
 {'id':'nmap-04','title':'Find the UDP management service','answer':'161','points':50,'hint':'Scan UDP and show open ports.','walkthrough':"""1. Run:\n\n   sudo nmap -sU --open -p 161 172.31.77.10\n\n2. Identify the exposed UDP service.\n3. Submit the port number."""},
 {'id':'nmap-05','title':'Identify the operating-system family','answer':'Linux','points':75,'hint':'Use Nmap OS fingerprinting with a guess enabled.','walkthrough':"""1. Run:\n\n   sudo nmap -O --osscan-guess 172.31.77.10\n\n2. Review the OS fingerprint.\n3. Submit the operating-system family reported."""},
 {'id':'nmap-06','title':'Use an NSE HTTP script','answer':'nginx','points':75,'hint':'Use the http-headers NSE script.','walkthrough':"""1. Run:\n\n   nmap --script http-headers 172.31.77.10\n\n2. Inspect the HTTP response headers.\n3. Identify the Server value.\n4. Submit the server product."""},
 {'id':'nmap-07','title':'Identify the mail software','answer':'Postfix','points':50,'hint':'Use service detection against SMTP.','walkthrough':"""1. Run:\n\n   nmap -sC -sV -p25 172.31.77.10\n\n2. Read the service/version information.\n3. Submit the mail software."""},
 {'id':'nmap-08','title':'Choose the raw-socket-free TCP scan','answer':'-sT','points':50,'hint':'This scan uses the normal TCP connect API and does not require raw-socket privileges.','walkthrough':"""1. Review TCP Connect scanning.\n2. The Nmap option is:\n\n   nmap -sT 172.31.77.10\n\n3. Submit the option."""}
],
'http':[
 {'id':'http-01','title':'Identify the web technology','answer':'nginx','points':50,'hint':'Inspect HTTP headers.','walkthrough':"""1. Run:\n\n   curl -I http://172.31.77.10\n\n2. Confirm with:\n\n   nmap -sV -sT -A 172.31.77.10\n\n3. Submit the web server technology."""},
 {'id':'http-02','title':'Recover the page identity via curl','answer':'ImranTheExploitHunter | OSCP-Style Practice Target','points':75,'hint':'Read the HTTP response body.','walkthrough':"""1. Fetch the page:\n\n   curl -s http://172.31.77.10\n\n2. Submit the exact identity string returned by the page."""}
],
'smb':[
 {'id':'smb-01','title':'Find the NetBIOS host name','answer':'ITEH-TARGET','points':50,'hint':'Query NetBIOS information.','walkthrough':"""1. Run:\n\n   nbtscan 172.31.77.10\n\n2. Find the registered machine name.\n3. Submit it."""},
 {'id':'smb-02','title':'Find the workgroup','answer':'WORKGROUP','points':50,'hint':'Use SMB metadata enumeration.','walkthrough':"""1. Run:\n\n   enum4linux-ng -A 172.31.77.10\n\n2. Locate Workgroup/Domain information.\n3. Submit the workgroup."""},
 {'id':'smb-03','title':'Find the anonymous share','answer':'Public','points':50,'hint':'Enumerate shares without credentials.','walkthrough':"""1. Run:

   smbclient -L //172.31.77.10 -N

2. Identify the guest-readable share.
3. Connect if needed:

   smbclient //172.31.77.10/Public -N

4. Submit the share name."""},
 {'id':'smb-04','title':'Identify the SMB protocol ports','answer':'139,445','points':50,'hint':'Scan the two classic SMB/NetBIOS TCP ports.','walkthrough':"""1. Run:\n\n   nmap -v -p 139,445 -oG smb.txt 172.31.77.10\n\n2. Confirm both ports are exposed.\n3. Submit them as `139,445`."""},
 {'id':'smb-05','title':'Find the SMB workgroup and OS: Windows 6.1 with OS discovery','answer':'Samba 4.17.12-Debian','points':75,'hint':'Use the SMB NSE OS discovery script and look specifically for the FQDN field.','walkthrough':"""1. Run:\n\n   nmap -v -p 139,445 --script smb-os-discovery 172.31.77.10\n\n2. Look for the OS: Windows 6.1 field in the NSE output.\n3. Submit the OS: Windows 6.1 value.\nExpected Answer: Samba 4.17.12-Debian"""}
],
'smtp':[
 {'id':'smtp-01','title':'Identify the SMTP hostname','answer':'mail.oscp.local','points':50,'hint':'Read the 220 SMTP banner.','walkthrough':"""1. Connect:\n\n   nc -nv 172.31.77.10 25\n\n2. Read the 220 greeting.\n3. Submit the hostname shown."""},
 {'id':'smtp-02','title':'Identify a valid SMTP user','answer':'root','points':75,'hint':'Compare VRFY responses for a known name and a bogus name.','walkthrough':"""1. Connect:\n\n   nc -nv 172.31.77.10 25\n\n2. Test:\n\n   VRFY root\n   VRFY idontexist\n\n3. `root` should receive a positive verification response, while `idontexist` should be rejected with a 550 response.\n4. Submit the valid username."""},
 {'id':'smtp-03','title':'Verify SMTP EXPN support','answer':'250 2.1.5 root <root@oscp.local>','points':50,'hint':'The lab SMTP service intentionally supports EXPN. Check the response for a valid list/user expansion.','walkthrough':"""1. Connect:\n\n   nc -nv 172.31.77.10 25\n\n2. Send:\n\n   EHLO oscp.local\n   EXPN root\n\n3. Confirm that EXPN is recognized and review the expansion response.\n4. Submit the response exactly as shown."""},
 {'id':'smtp-04','title':'Identify the traditional SMTP port','answer':'25','points':50,'hint':'The SMTP service is exposed on the traditional TCP service port.','walkthrough':"""1. Use Nmap service detection:\n\n   nmap -sC -sV -p25 172.31.77.10\n\n2. Confirm SMTP.\n3. Submit the port."""}
],
'snmp':[
 {'id':'snmp-01','title':'Identify the SNMP hostname via snmpwalk','answer':'target','points':50,'hint':'Query the standard system tree with the read-only community.','walkthrough':"""1. Run:\n\n   snmpwalk -v2c -c public 172.31.77.10 1.3.6.1.2.1.1\n\n2. Find sysName (1.3.6.1.2.1.1.5).\n3. Submit the hostname."""},
 {'id':'snmp-02','title':'Extract the system description via snmpwalk','answer':'Linux ITEH OSCP Practice Target','points':50,'hint':'Query sysDescr.','walkthrough':"""1. Run:\n\n   snmpwalk -v2c -c public 172.31.77.10 1.3.6.1.2.1.1.1.0\n\n2. Read the returned value.\n3. Submit the exact description."""},
 {'id':'snmp-03','title':'Extract the system location via snmpwalk','answer':'OSCP Practice Lab','points':50,'hint':'Query sysLocation.','walkthrough':"""1. Run:\n\n   snmpwalk -v2c -c public 172.31.77.10 1.3.6.1.2.1.1.6.0\n\n2. Read the returned value.\n3. Submit the exact location."""},
 {'id':'snmp-04','title':'Discover the SNMP community','answer':'public','points':75,'hint':'The lab intentionally uses a common read-only community string.','walkthrough':"""1. Discover UDP/161:\n\n   sudo nmap -sU --open -p 161 172.31.77.10\n\n2. Prepare a small community list:\n\n   printf \"public\\nprivate\\nmanager\\n\" > community\n\n3. Use onesixtyone:\n\n   printf '172.31.77.10\n' > ips\n   onesixtyone -c community -i ips\n\n4. Identify the accepted read-only community."""},
 {'id':'snmp-05','title':'Enumerate running processes via snmpwalk','answer':'snmpd','points':75,'hint':'Walk the HOST-RESOURCES-MIB process table.','walkthrough':"""1. Run:\n\n   snmpwalk -v2c -c public 172.31.77.10 1.3.6.1.2.1.25.4.2.1.2\n\n2. Review process-name values.\n3. Find the SNMP daemon.\n4. Submit the process name."""},
 {'id':'snmp-06','title':'Enumerate installed software context via snmpwalk','answer':'nginx','points':75,'hint':'Query the installed software table and look for the web server package.','walkthrough':"""1. Run:\n\n   snmpwalk -v2c -c public 172.31.77.10 1.3.6.1.2.1.25.6.3.1.2\n\n2. Review software descriptions.\n3. Identify the web-server software.\n4. Submit its name."""},
 {'id':'snmp-07','title':'Enumerate listening 80 TCP port open or not via snmpwalk ','answer':'80 open','points':75,'hint':'Query the TCP connection table and look for a listening local endpoint.','walkthrough':"""1. Run:\n\n   snmpwalk -v2c -c public 172.31.77.10 1.3.6.1.2.1.6.13.1.3\n\n2. Inspect local-port values.\n3. Identify the web service port.\n4. Submit the port number open.\n\nNote: host-level data can reveal useful context beyond an external scan."""}
],
'dns':[
 {'id':'dns-01','title':'Resolve the domain to IPv4','answer':'172.31.77.10','points':50,'hint':'Query the lab DNS server explicitly.','walkthrough':"""1. Run:\n\n   host oscp.local 172.31.77.2\n\n2. Read the A record.\n3. Submit the IPv4 address.\n\nNote: `host oscp.local` alone uses Kali's normal resolver; the isolated lab DNS is 172.31.77.2."""},
 {'id':'dns-02','title':'Find the mail exchanger','answer':'mail.oscp.local','points':50,'hint':'Query MX.','walkthrough':"""1. Run:\n\n   host -t MX oscp.local 172.31.77.2\n\n2. Submit the mail exchanger hostname."""},
 {'id':'dns-03','title':'Find the SPF TXT record','answer':'v=spf1 ip4:172.31.0.0/16 ~all','points':50,'hint':'Query TXT records.','walkthrough':"""1. Run:\n\n   host -t TXT oscp.local 172.31.77.2\n\n2. Submit the SPF value exactly."""},
 {'id':'dns-04','title':'Test a nonexistent hostname','answer':'idontexist','points':50,'hint':'Query a deliberately invalid hostname.','walkthrough':"""1. Run:\n\n   host idontexist.oscp.local 172.31.77.2\n\n2. Observe the NXDOMAIN response.\n3. Submit the hostname.\nExpected Answer: idontexist"""},
 {'id':'dns-05','title':'Discover the target with reverse DNS','answer':'172.31.77.10','points':75,'hint':'Use a reverse lookup loop against the lab /24.','walkthrough':"""1. Run:\n\n   for ip in $(seq 1 254); do host 172.31.77.$ip 172.31.77.2; done \n\n2. Review the PTR responses.\n3. Find the response for target.oscp.local.\n4. The matching IP is 172.31.77.10.\n5. Submit the IP address.\nExpected Answer: 172.31.77.10"""},
 {'id':'dns-06','title':'Run DNSRecon standard enumeration','answer':'mail.oscp.local','points':50,'hint':'Use dnsrecon standard mode and the lab DNS server.','walkthrough':"""1. Run:\n\n   dnsrecon -d oscp.local -n 172.31.77.2 -t std\n\n2. Review NS/MX/TXT/A records.\n3. Submit the mail host."""},
 {'id':'dns-07','title':'Brute-force DNS to find an interesting hostname','answer':'dev.oscp.local','points':75,'hint':'Use dnsrecon brute-force mode and look for a hostname that suggests source-code or developer infrastructure.','walkthrough':"""1. Run:\n\n   dnsrecon -d oscp.local -n 172.31.77.2 -D /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -t brt\n\n2. Review discovered A records.\n3. Look for the interesting source-control hostname.\n4. Submit the interesting A record."""},
 {'id':'dns-08','title':'Enumerate with dnsenum','answer':'ns.oscp.local','points':50,'hint':'Use dnsenum and point it at the lab DNS server.','walkthrough':"""1. Run:\n\n   dnsenum --dnsserver 172.31.77.2 oscp.local\n\n2. Identify the authoritative nameserver.\n3. Submit its hostname."""},
 {'id':'dns-09','title':'Identify the authoritative DNS server','answer':'ns.oscp.local','points':50,'hint':'Inspect the NS record.','walkthrough':"""1. Run:\n\n   host -t NS oscp.local 172.31.77.2\n\n2. Submit the nameserver hostname."""}
],
'windows-enum':[
 {'id':'win-01','title':'Built-in Windows TCP check','answer':'Test-NetConnection','points':50,'hint':'Think of the PowerShell function used when Nmap is unavailable.','walkthrough':"""1. The built-in PowerShell function is:\n\n   Test-NetConnection -Port 445 192.168.50.151\n\n2. Its TcpTestSucceeded field reports whether the TCP connection succeeded.\n3. Submit the function name."""},
 {'id':'win-02','title':'Identify the PowerShell port-loop keyword','answer':'foreach','points':50,'hint':'The lesson iterates through ports 1..1024.','walkthrough':"""1. Review the pattern:\n\n   foreach ($port in 1..1024) { ... }\n\n2. Submit the loop keyword."""}
]
}


class WalkthroughRequest(BaseModel):
    password:str=Field(max_length=64)

class Submission(BaseModel):
    challenge_id:str
    answer:str=Field(max_length=500)

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS submissions (challenge_id TEXT PRIMARY KEY,module TEXT,answer TEXT,correct INTEGER,points INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
        c.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY,value TEXT)')

def client():
    try: return docker.from_env()
    except Exception as e: raise HTTPException(503,f'Container engine unavailable: {e}')

def get_container(name):
    try:return client().containers.get(name)
    except docker.errors.NotFound:return None

def ensure_network():
    cli=client()
    try:return cli.networks.get(NETWORK)
    except docker.errors.NotFound:
        return cli.networks.create(NETWORK,driver='bridge',internal=False,ipam=docker.types.IPAMConfig(pool_configs=[docker.types.IPAMPool(subnet=SUBNET)]),labels={'brand':'ImranTheExploitHunter','mode':'OSCP-style'})

def run_one(cli,image,name,ip,role,env=None,mem='384m',cpu=50000,pids=192):
    old=get_container(name)
    if old:
        try: old.remove(force=True)
        except Exception: pass
    net=cli.networks.get(NETWORK)
    c=cli.containers.create(image,name=name,detach=True,environment=env or {},mem_limit=mem,cpu_quota=cpu,pids_limit=pids,labels={'brand':'ImranTheExploitHunter','role':role,'training':'oscp-style'})
    # Explicitly pin the lab address so the dashboard target IP matches reality.
    net.connect(c, ipv4_address=ip, aliases=[name])
    c.start()
    return c

def provision():
    cli=client(); ensure_network()
    run_one(cli,TARGET_IMAGE,'ith-oscp-target',TARGET,'target',mem='384m')
    run_one(cli,DNS_IMAGE,'ith-oscp-dns',DNS,'dns',{'TARGET_IP':TARGET,'DNS_IP':DNS},mem='256m',pids=128)
    with db() as c:c.execute("INSERT OR REPLACE INTO state(key,value) VALUES('status','running')")
    return {'status':'running','subnet':SUBNET,'target_ip':TARGET,'dns_ip':DNS,'targets':[{'name':'OSCP Practice Target','ip':TARGET,'services':['22/tcp','25/tcp','80/tcp','139/tcp','445/tcp','161/udp']},{'name':'Lab DNS','ip':DNS,'services':['53/tcp','53/udp']} ]}

def stop(reset=False):
    cli=client()
    for n in ('ith-oscp-target','ith-oscp-dns'):
        c=get_container(n)
        if c:
            try:c.remove(force=True)
            except Exception:pass
    if reset:
        try:cli.networks.get(NETWORK).remove()
        except Exception:pass
        with db() as c:c.execute('DELETE FROM submissions');c.execute('DELETE FROM state')
    else:
        with db() as c:c.execute("INSERT OR REPLACE INTO state(key,value) VALUES('status','stopped')")

@app.on_event('startup')
def startup():init_db()
@app.get('/health')
def health():return {'status':'ok','branding':'ImranTheExploitHunter','mode':'OSCP-style local training'}
@app.get('/modules')
def modules():
    return {m:[{k:v for k,v in x.items() if k not in ('answer','walkthrough')} for x in cs] for m,cs in MODULES.items()}
@app.post('/walkthrough/{challenge_id}')
def walkthrough(challenge_id:str, req:WalkthroughRequest):
    if req.password != 'ITEH':
        raise HTTPException(403,'Invalid walkthrough password')
    for cs in MODULES.values():
        for c in cs:
            if c['id']==challenge_id:return {'id':challenge_id,'title':c['title'],'walkthrough':c['walkthrough'],'expected_answer':c['answer']}
    raise HTTPException(404,'Challenge not found')
@app.post('/lab/start')
def start():return provision()
@app.post('/lab/stop')
def stop_lab():stop(False);return {'status':'stopped'}
@app.post('/lab/reset')
def reset_lab():stop(True);return provision()
@app.get('/lab/status')
def status():
    with db() as c:r=c.execute("SELECT value FROM state WHERE key='status'").fetchone()
    st=r[0] if r else 'not_created'
    target=get_container('ith-oscp-target')
    if target and target.status=='running':st='running'
    return {'status':st,'subnet':SUBNET,'target_ip':TARGET if st=='running' else None,'dns_ip':DNS if st=='running' else None}
@app.post('/submit')
def submit(s:Submission):
    found=next(((m,c) for m,cs in MODULES.items() for c in cs if c['id']==s.challenge_id),None)
    if not found:raise HTTPException(404,'Challenge not found')
    m,c=found;ok=s.answer.strip().lower()==c['answer'].strip().lower();pts=c['points'] if ok else 0
    with db() as x:x.execute('INSERT OR REPLACE INTO submissions(challenge_id,module,answer,correct,points) VALUES(?,?,?,?,?)',(s.challenge_id,m,s.answer,1 if ok else 0,pts))
    return {'correct':ok,'points':pts,'message':'Correct!' if ok else 'Incorrect answer.'}
@app.get('/submissions')
def submissions():
    with db() as c:
        rows=c.execute('SELECT challenge_id,module,answer,correct,points FROM submissions').fetchall()
    return {'submissions':[dict(r) for r in rows]}

@app.get('/score')
def score():
    possible=sum(c['points'] for cs in MODULES.values() for c in cs)
    with db() as c:points=c.execute('SELECT COALESCE(SUM(points),0) FROM submissions WHERE correct=1').fetchone()[0];done=c.execute('SELECT COUNT(*) FROM submissions WHERE correct=1').fetchone()[0]
    return {'points':points,'completed':done,'possible':possible,'percent':round(points*100/possible,1)}
