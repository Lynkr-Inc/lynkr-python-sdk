from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import os
import base64
import json

def load_public_key(pem_path: str):
    with open(pem_path, "rb") as key_file:
        return serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )

def encrypt_with_aes(data: bytes, key: bytes):
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key), modes.GCM(iv), backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return (ciphertext, iv, encryptor.tag)

def encrypt_key_with_rsa(key: bytes, public_key):
    encrypted = public_key.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted

def hybrid_encrypt(payload: dict, public_key):
    # 1. Serialize payload to bytes
    data = json.dumps(payload).encode()

    # 2. Generate AES key
    aes_key = os.urandom(32)  # AES-256

    # 3. Encrypt data with AES
    ciphertext, iv, tag = encrypt_with_aes(data, aes_key)

    # 4. Encrypt AES key with RSA public key
    encrypted_key = encrypt_key_with_rsa(aes_key, public_key)

    # 5. Return base64-encoded fields
    return {
        "encrypted_key": base64.b64encode(encrypted_key).decode(),
        "iv": base64.b64encode(iv).decode(),
        "tag": base64.b64encode(tag).decode(),
        "payload": base64.b64encode(ciphertext).decode(),
    }, aes_key

def decrypt_with_aes(ciphertext, key, iv, tag):
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag)
    ).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()