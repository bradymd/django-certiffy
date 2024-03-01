# Import the cryptography library and its modules
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from .readcert import readcert
from cryptography.hazmat.backends import default_backend

import sys
def gencertsr(data):
    # Generate a private key using RSA algorithm and 2048 bits
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Create a CSR object with the common name and other attributes

    # concoct list of fields Nameattributes 
    attributes_array=[]
    for d in data:
        if  data[d] != "" and \
            d != 'subject_alternative_name' and \
            d != 'issuer':
          attributes_array.append( eval(f'x509.NameAttribute(NameOID.{d.upper()}, "{data[d]}")'))

    # concoct list of the alternate names 
    alternate_array=[]
    """Although the use of the Common Name is existing practice, it is deprecated and Certification Authorities are encouraged to use the dNSName instead."""
    if data['common_name'] not in data['subject_alternative_name']:
        data['subject_alternative_name'].append(data['common_name'])

    for l in  data['subject_alternative_name']:
                alternate_array.append( eval(f'x509.DNSName("{l}")'))

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name( 
               attributes_array
            )
        )
        .add_extension(
            x509.SubjectAlternativeName(
                alternate_array
            ),
           critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    pemkey=private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode('UTF-8')
    pemcsr=csr.public_bytes(serialization.Encoding.PEM).decode('UTF-8')

    c = x509.load_pem_x509_csr(csr.public_bytes(serialization.Encoding.PEM), default_backend())
    return pemcsr,pemkey,csr

