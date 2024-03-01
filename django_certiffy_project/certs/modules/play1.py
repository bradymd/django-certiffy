from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import AttributeOID, NameOID, ExtensionOID

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
builder = x509.CertificateSigningRequestBuilder()

#This can only be set once, so you have to have the array 
#fully assembled
name_attributes_list =[ 
     x509.NameAttribute(NameOID.COMMON_NAME, 'sonic.fabio.org.uk'),
     x509.NameAttribute(NameOID.LOCALITY_NAME, 'Hemel Hempstead'), 
     ]

builder = builder.subject_name(x509.Name(name_attributes_list ))

builder = builder.add_extension(
    x509.BasicConstraints(ca=False, path_length=None), critical=True,
)

request = builder.sign(
    private_key, hashes.SHA256()
    )

isinstance(request, x509.CertificateSigningRequest)
print(request.encode('UTF-8'))

