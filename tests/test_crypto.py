from agora.crypto import decrypt, encrypt


def test_crypto():
    msg = "Secret Message"
    pwd = "my_secure_password"
    enc_data = encrypt(msg, pwd)
    dec_msg = decrypt(enc_data, pwd)
    assert dec_msg == msg
