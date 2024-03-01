import ssl
import socket
import sys
import requests
hostname , port = 'helpdesk.herts.ac.uk', 443 # works
hostname , port = 'helpdesk.herts.ac.uk', 8443 # no works

import requests

#context = ssl.create_default_context()
context = ssl._create_unverified_context()
#context.check_hostname = False
#context.verify_mode = ssl.CERT_NONE
#context.set_alpn_protocols(['h2', 'spdy/3', 'http/1.1'])

# CREATE SOCKET
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(100)
wrappedSocket = context.wrap_socket(sock, server_hostname=hostname)
print('this connection fails')
wrappedSocket.connect((hostname,port))
print('huh')
cert = wrappedSocket.getpeercert()
print(cert)
# Create a socket object
sys.exit()
sock =  socket.create_connection((hostname, int(port)),
                                 timeout=2,
                                 prxy_rdns=True
                                 ) 
sock.connect(hostname, port)

# Wrap the socket with SSL
try:
    wrappedSocket = context.wrap_socket(sock, server_hostname=hostname )
except ssl.SSLError as e:
    print(e)
    print("error")
    sys.exit()

# Get the certificate in binary DER format
der_cert = wrappedSocket.getpeercert(True)
#print(der_cert)
print('fine')
# Close the socket
wrappedSocket.close()

sys.exit()

from cryptography import x509
import socket
import ssl
import sys
from datetime import datetime,timezone
import pytz
def checkexpiry( hostname, port, expirydate ):
    # create default context
    context = ssl.create_default_context()
    #context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain(certfile="/tmp/cert.pem", keyfile="/tmp/key.pem")

    # override context so that it can get expired cert
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        print(f'about to connect to {hostname}:{port}')
        with socket.create_connection((hostname, int(port)),timeout=2) as sock:
            print(f'about to context.wrap_socket')
            """
            socketHandler = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socketWraped = ssl.create_default_context().wrap_socket(socketHandler, server_hostname='certificatedetails.com')
            socketWraped.connect(('certificatedetails.com', 443))]
        """
            with context.wrap_socket(sock, server_hostname=hostname ) as ssock:
                # get cert in DER format
                print('about to getpeercert')
                data = ssock.getpeercert(True)
                print(f'Did we reach here? {data}')
                # convert cert to PEM format
                pem_data = ssl.DER_cert_to_PEM_cert(data)
                # pem_data in string. convert to bytes using str.encode()
                # extract cert info from PEM format
                try:
                  cert_data = x509.load_pem_x509_certificate(str.encode(pem_data))
                except:
                  print('x509.load_pem_x509_certificate error')
                expirydate=cert_data.not_valid_after
                utcexpirydate = expirydate.replace(tzinfo=pytz.utc)
                utcnow = datetime.now(timezone.utc)
                daystogo = ( utcexpirydate - utcnow).days
                return True,daystogo,utcexpirydate
    except ssl.SSLError as e :
        print(e)
        utcnow = datetime.now(timezone.utc)
        utcexpirydate = expirydate.replace(tzinfo=pytz.utc)
        daystogo = (utcexpirydate - utcnow).days
        return False,daystogo,utcexpirydate

