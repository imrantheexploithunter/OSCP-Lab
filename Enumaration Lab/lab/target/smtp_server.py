#!/usr/bin/env python3
import socket
import threading

HOST='0.0.0.0'; PORT=25
BANNER='220 mail.oscp.local ESMTP Postfix ITEH-Training'
USERS={'root'}

def handle(conn, addr):
    try:
        conn.sendall((BANNER+'\r\n').encode())
        while True:
            data=conn.recv(4096)
            if not data: break
            line=data.decode(errors='ignore').strip()
            upper=line.upper()
            if upper.startswith('EHLO') or upper.startswith('HELO'):
                resp='250-mail.oscp.local\r\n250-PIPELINING\r\n250-SIZE 10240000\r\n250-VRFY\r\n250-EXPN\r\n250-ETRN\r\n250-ENHANCEDSTATUSCODES\r\n250-8BITMIME\r\n250-DSN\r\n250 CHUNKING\r\n'
                conn.sendall(resp.encode())
            elif upper.startswith('VRFY '):
                user=line[5:].strip().split()[0] if line[5:].strip() else ''
                if user.lower() in USERS:
                    conn.sendall(b'252 2.0.0 root <root@oscp.local>\r\n')
                else:
                    conn.sendall(b'550 5.1.1 User unknown\r\n')
            elif upper.startswith('EXPN '):
                user=line[5:].strip().split()[0] if line[5:].strip() else ''
                if user.lower() in USERS:
                    conn.sendall(b'250 2.1.5 root <root@oscp.local>\r\n')
                else:
                    conn.sendall(b'550 5.1.1 List unknown\r\n')
            elif upper == 'QUIT':
                conn.sendall(b'221 2.0.0 Bye\r\n'); break
            elif upper in ('NOOP','RSET'):
                conn.sendall(b'250 2.0.0 OK\r\n')
            else:
                conn.sendall(b'502 5.5.1 Command not implemented\r\n')
    except Exception:
        pass
    finally:
        try: conn.close()
        except: pass

def main():
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((HOST,PORT)); s.listen(50)
    while True:
        c,a=s.accept(); threading.Thread(target=handle,args=(c,a),daemon=True).start()
if __name__=='__main__': main()
