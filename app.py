from flask import Flask, render_template, request
import qrcode
import io
import base64

app = Flask(__name__)

# RSA Parametreleri
P = 61
Q = 53
N = P * Q            # 3233
E = 17               
D = 2753             

def rsa_encrypt(text):
    try:
        encrypted_blocks = []
        for char in text:
            m = ord(char)
            c = pow(m, E, N)
            encrypted_blocks.append(str(c))
        return "-".join(encrypted_blocks)
    except Exception:
        return ""

def rsa_decrypt(cipher_text):
    try:
        if not cipher_text:
            return ""
        blocks = cipher_text.split("-")
        decrypted_chars = []
        for block in blocks:
            if block.isdigit():
                c = int(block)
                m = pow(c, D, N)
                decrypted_chars.append(chr(m))
        return "".join(decrypted_chars)
    except Exception:
        return "[Geçersiz Şifre Formatı]"

# Ana sayfa: Şifreleme ve QR Üretimi
@app.route("/", methods=["GET", "POST"])
def index():
    qr_code_base64 = None
    share_url = None
    encrypted_data = None
    
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

    return render_template("generator.html", qr_code=qr_code_base64, share_url=share_url, encrypted_data=encrypted_data)

# QR Kod Okutulduğunda Otomatik Çözen Sayfa
@app.route("/coz")
def coz():
    cipher_data = request.args.get("data", "")
    decrypted_text = rsa_decrypt(cipher_data)
    is_valid = bool(cipher_data and decrypted_text != "[Geçersiz Şifre Formatı]")
    
    return render_template("solve.html", cipher_data=cipher_data, is_valid=is_valid, decrypted_text=decrypted_text)

# YENİ SAYFA: Şifreyi Kutuya Yazıp Çözebileceğin Manuel Çözücü
@app.route("/cozumle", methods=["GET", "POST"])
def manuel_cozumle():
    decrypted_result = None
    cipher_input = ""
    
    if request.method == "POST":
        cipher_input = request.form.get("cipher_text", "")
        if cipher_input:
            decrypted_result = rsa_decrypt(cipher_input)
            
    return render_template("manuel_solve.html", decrypted_result=decrypted_result, cipher_input=cipher_input)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
