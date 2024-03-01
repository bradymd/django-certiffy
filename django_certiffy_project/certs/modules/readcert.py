import ssl, sys
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
from cryptography.hazmat.backends import default_backend

def readcert(url, port):
    print(url,port)
    data = {}
    try:
        c = ssl.get_server_certificate((url, port))
    except:
        return data
    cert = x509.load_pem_x509_certificate(bytes(c, "UTF-8"))
    issuer=cert.issuer
    cn = issuer.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    o = issuer.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)[0].value
    data['issuer'] = f"{cn},{o}"

    common_name = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[
        0
    ].value
    data["common_name"] = common_name
    try:
        country_name = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COUNTRY_NAME)[
        0
    ].value
    except:
        country_name = ""
    data["country_name"] = country_name
    try:
        state_or_province_name = cert.subject.get_attributes_for_oid(
         x509.oid.NameOID.STATE_OR_PROVINCE_NAME
        )[0].value
    except:
        state_or_province_name = ""
    data["state_or_province_name"] = state_or_province_name
    try:
        locality_name = cert.subject.get_attributes_for_oid(
            x509.oid.NameOID.LOCALITY_NAME
        )[0].value
    except:
        locality_name = ""
    data["locality_name"] = locality_name
    try:
        organization_name = cert.subject.get_attributes_for_oid(
          x509.oid.NameOID.ORGANIZATION_NAME
        )[0].value
    except:
        organization_name = ""
    data["organization_name"] = organization_name
    ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    subject_alternative_name = ext.value.get_values_for_type(x509.DNSName)
    data["subject_alternative_name"] = ','.join(subject_alternative_name)
    try:
        organizational_unit_name = cert.subject.get_attributes_for_oid(
            x509.oid.NameOID.ORGANIZATIONAL_UNIT_NAME
        )[0].value
    except:
        organizational_unit_name = ""
    data["organizational_unit_name"] = organizational_unit_name
    try:
        email_address = cert.subject.get_attributes_for_oid(
         x509.oid.NameOID.EMAIL_ADDRESS
        )[0].value
    except:
        email_address=""
    data["email_address"] = email_address
    return data

