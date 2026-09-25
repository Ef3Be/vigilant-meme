from flask import Flask, render_template, request
import qrcode
import io
import base64
from cryptography.fernet import Fernet

app = Flask(__name__)

# Sabit bir anahtar oluşturuyoruz (Gerçek projelerde güvenli saklanır, 
# proje prototipi için bu sabit anahtar her sunucu yeniden başlatıldığında verinin çözülebilmesini sağlar)
# Fernet 32 baytlık url-safe base64 encoded anahtar ister:
SECRET_KEY = b'12345678901234567890123456789012=' # 32 baytlık sabit bir temel
# Güvenli Fernet anahtarı türetelim:
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import pbkdf2_hmac

# Prototip için sabit ve kararlı bir anahtar türetiyoruz:
kdf = pbkdf2_hmac(
    hashes.SHA256(),
    length=32,
    salt=b'tubitak_guvenli_qr_salt',
    iterations=100_000,
)
key = base64.urlsafe_b64encode(kdf)
cipher_suite = Fernet(key)

def rsa_encrypt(text):
    try:
        # Fernet kullanarak metni şifreliyoruz (AES tabanlı simetrik şifreleme)
        encrypted_bytes = cipher_suite.encrypt(text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception:
        return ""

def rsa_decrypt(cipher_text):
    try:
        if not cipher_text:
            return ""
        decrypted_bytes = cipher_suite.decrypt(cipher_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        return "[Geçersiz Şifre Formatı]"

@app.route("/", methods=["GET", "POST"])
def index():
    qr_code_base64 = None
    share_url = None
    
    if request.method == "POST":
        user_text = request.form.get("text", "")
        if user_text:
            encrypted_data = rsa_encrypt(user_text)
            base_url = request.host_url.rstrip('/')
            target_url = f"{base_url}/coz?data={encrypted_data}"
            share_url = target_url
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(target_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return render_template("generator.html", qr_code=qr_code_base64, share_url=share_url)

@app.route("/coz")
def coz():
    cipher_data = request.args.get("data", "")
    
    # Verinin bu sisteme ait ve bütünlüğünün bozulmamış olduğunu test ediyoruz
    decrypted_text = rsa_decrypt(cipher_data)
    is_valid = bool(cipher_data and decrypted_text != "[Geçersiz Şifre Formatı]")
    
    return render_template("solve.html", cipher_data=cipher_data, is_valid=is_valid, decrypted_text=decrypted_text)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
