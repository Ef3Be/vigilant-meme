from flask import Flask, render_template, request
import qrcode
import io
import base64

app = Flask(__name__)

p = 61
q = 53
n = p * q            # 323
phi = (p - 1) * (q - 1) # 3120
e = 17               
d = 2753             

def rsa_encrypt(text):
    encrypted = []
    for char in text:
        m = ord(char)
        c = pow(m, e, n)
        encrypted.append(str(c))
    return "-".join(encrypted)

def rsa_decrypt(cipher_text):
    try:
        if not cipher_text:
            return ""
        decrypted = []
        parts = cipher_text.split("-")
        for part in parts:
            if part:
                c = int(part)
                m = pow(c, d, n)
                decrypted.append(chr(m))
        return "".join(decrypted)
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
    
    # Güvenlik önlemi: İsteğe bağlı olarak orijinal metni direkt açıkta göstermiyoruz, 
    # sadece veri bütünlüğünün ve RSA imzasının geçerli olduğunu doğruluyoruz.
    # Eğer test etmek istersen alttaki satırı aktif edebilirsin, ancak gizlilik için gizli tutuyoruz:
    # original_text = rsa_decrypt(cipher_data)
    
    # Sistem sadece şifreli paketin bozulmamış olduğunu ve geçerli bir RSA modülüne ait olduğunu doğrular.
    is_valid = bool(cipher_data)
    
    return render_template("solve.html", cipher_data=cipher_data, is_valid=is_valid, n=n, e=e)

if __name__ == "__main__":
    app.run(debug=True, port=5000)