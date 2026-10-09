from flask import Flask, render_template, request
import qrcode
import io
import base64
import time

app = Flask(__name__)

# RSA Parametreleri
P = 61
Q = 53
N = 3233  # P * Q
PHI = 3120 # (P-1) * (Q-1)
E = 17
D = 2753   # Gizli anahtar

EXPIRATION_TIME = 4 * 60  # 4 dakika süre sınırı

def encrypt(text):
    encrypted = [str(pow(ord(char), E, N)) for char in text]
    return "-".join(encrypted)

def decrypt(encrypted_str):
    try:
        parts = encrypted_str.split("-")
        decrypted = "".join([chr(pow(int(p), D, N)) for p in parts])
        return decrypted
    except Exception:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    qr_code = None
    cipher_text = ""
    if request.method == "POST":
        plain_text = request.form.get("plain_text")
        if plain_text:
            c_text = encrypt(plain_text)
            current_time = int(time.time())
            full_payload = f"{c_text}|{current_time}"
            
            # QR kodun içine doğrudan /coz linkini gömüyoruz
            # (Render'daki güncel domain adresine göre otomatik algılar veya tam URL yazabilirsin)
            base_url = request.host_url.rstrip('/')
            qr_target_url = f"{base_url}/coz?data={full_payload}"
            
            img = qrcode.make(qr_target_url)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            qr_code = base64.b64encode(buffered.getvalue()).decode("utf-8")
            cipher_text = full_payload
            
    return render_template("generator.html", qr_code=qr_code, cipher_text=cipher_text)

@app.route("/coz")
def coz():
    data = request.args.get("data", "")
    if not data:
        return render_template("solve.html", error="VERİ BULUNAMADI!", decrypted=None)
    
    try:
        if "|" in data:
            c_text, timestamp_str = data.rsplit("|", 1)
            msg_time = int(timestamp_str)
            current_time = int(time.time())
            
            if current_time - msg_time > EXPIRATION_TIME:
                return render_template("solve.html", error="[!] HATA: QR KODUN SÜRESİ DOLDU! (4 Dakikalık TTL Sınırı Aşıldı)", decrypted=None, cipher_data=c_text)
        else:
            c_text = data
            
        decrypted = decrypt(c_text)
        if decrypted is None:
            return render_template("solve.html", error="[!] ŞİFRE ÇÖZÜLEMEDİ (Hatalı Format)", decrypted=None, cipher_data=c_text)
            
        return render_template("solve.html", decrypted=decrypted, error=None, cipher_data=c_text)
    except Exception as e:
        return render_template("solve.html", error=f"[!] KRİTİK HATA: {str(e)}", decrypted=None, cipher_data=data)

@app.route("/cozumle", methods=["GET", "POST"])
def manuel_cozumle():
    decrypted_result = None
    cipher_input = ""
    if request.method == "POST":
        cipher_input = request.form.get("cipher_text", "").strip()
        if cipher_input:
            try:
                if "|" in cipher_input:
                    c_text, timestamp_str = cipher_input.rsplit("|", 1)
                    msg_time = int(timestamp_str)
                    current_time = int(time.time())
                    if current_time - msg_time > EXPIRATION_TIME:
                        decrypted_result = "[!] HATA: GİRİLEN VERİNİN SÜRESİ DOLMUŞ!"
                    else:
                        decrypted_result = decrypt(c_text)
                else:
                    decrypted_result = decrypt(cipher_input)
            except Exception:
                decrypted_result = "[!] ÇÖZÜMLEME BAŞARISIZ."
                
    return render_template("manuel_solve.html", decrypted_result=decrypted_result, cipher_input=cipher_input)

if __name__ == "__main__":
    app.run(debug=True)
