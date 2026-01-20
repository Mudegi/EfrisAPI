from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PublicFormat
import os

cert_path = "keys/wandera.pfx"
password = b'123456'

with open(cert_path, 'rb') as f:
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(f.read(), password)

# Extract public key from certificate
public_key = certificate.public_key()

# Save public key in PEM format (what EFRIS expects)
public_pem = public_key.public_bytes(
    encoding=Encoding.PEM,
    format=PublicFormat.SubjectPublicKeyInfo
)

print("=" * 80)
print("PUBLIC KEY (PEM FORMAT)")
print("=" * 80)
print(public_pem.decode())

#Save to file
with open("keys/public_key.pem", "wb") as f:
    f.write(public_pem)
    
print("\n✓ Public key saved to keys/public_key.pem")
print("\nUpload this public key to EFRIS portal for your device 1014409555_02")
