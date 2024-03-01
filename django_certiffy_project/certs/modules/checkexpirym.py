from cryptography import x509
import socket, ssl
import sys, logging
from datetime import datetime,timezone
import pytz

logging.basicConfig(level=logging.WARN,format='%(process)-%(levelname)s-%(message)s')
# use logging.debug(), logging.warn(), logging.info()

def checkexpiry( hostname, port, expirydate ):
    # create default context
    context = ssl.create_default_context()
    #context = ssl._create_unverified_context()
    # override context so that it can get expired cert
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((hostname, int(port)),timeout=4) as sock:
            with context.wrap_socket(sock, server_hostname=hostname ) as ssock:
                # get cert in DER format
                data = ssock.getpeercert(True)
                # convert cert to PEM format
                pem_data = ssl.DER_cert_to_PEM_cert(data)
                # pem_data in string. convert to bytes using str.encode()
                # extract cert info from PEM format
                try:
                  cert_data = x509.load_pem_x509_certificate(str.encode(pem_data))
                except:
                  logging.debug('x509.load_pem_x509_certificate error')
                expirydate=cert_data.not_valid_after
                utcexpirydate = expirydate.replace(tzinfo=pytz.utc)
                utcnow = datetime.now(timezone.utc)
                daystogo = ( utcexpirydate - utcnow).days
                return True,daystogo,utcexpirydate
    except Exception as e:
        logging.debug(f'{datetime.now(timezone.utc)} {hostname}:{port} TimeoutError {e}')
        utcnow = datetime.now(timezone.utc)
        utcexpirydate = expirydate.replace(tzinfo=pytz.utc)
        daystogo = (utcexpirydate - utcnow).days
        return False,daystogo,utcexpirydate

