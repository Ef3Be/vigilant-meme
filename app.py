from flask import Flask, render_template, request
import qrcode
import io
import base64
import time

app = Flask(__name__)

# RSA Parametreleri
P = 61
Q = 53
N = 3233   # P * Q
PHI = 3120 # (P - 1) * (Q - 1)
E = 17
D = 2753

EXPIRATION_TIME = 4 * 60  # 240 saniye (4 dakika)


def encrypt(text: str) -> str:
    encrypted = [str(pow(ord(char), E, N)) for char in text]
    return "-".join(encrypted)


def decrypt(encrypted_str: str):
    try:
        parts = encrypted_str.strip().split("-")
        decrypted = "".join([chr(pow(int(p), D, N)) for p in parts])
        return decrypted
    except Exception:
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    qr_code = None
    verify_url = None
    cipher_payload = None
    error = None

    if request.method == "POST":
        plain_text = request.form.get("plain_text", "").strip()
        if plain_text:
            c_text = encrypt(plain_text)
            current_time = int(time.time())
            full_payload = f"{c_text}|{current_time}"

            base_url = request.host_url.rstrip("/")
            verify_url = f"{base_url}/coz?data={full_payload}"
            cipher_payload = full_payload

            img = qrcode.make(verify_url)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            qr_code = base64.b64encode(buffered.getvalue()).decode("utf-8")
        else:
            error = "Lütfen şifrelenecek geçerli bir metin veya kelime girin."

    return render_template(
        "generator.html",
        qr_code=qr_code,
        verify_url=verify_url,
        cipher_payload=cipher_payload,
        error=error,
    )


@app.route("/coz")
def coz():
    data = request.args.get("data", "").strip()
    if not data:
        return render_template(
            "solve.html",
            error="Doğrulama verisi bulunamadı.",
            cipher_data=None,
            remaining_seconds=None,
        )

    try:
        if "|" in data:
            c_text, timestamp_str = data.rsplit("|", 1)
            msg_time = int(timestamp_str)
            current_time = int(time.time())
            elapsed = current_time - msg_time

            if elapsed > EXPIRATION_TIME:
                return render_template(
                    "solve.html",
                    error="Bu karekodun ve bağlantının 4 dakikalık geçerlilik süresi dolmuştur.",
                    cipher_data=c_text,
                    remaining_seconds=0,
                )

            remaining = max(0, EXPIRATION_TIME - elapsed)
            return render_template(
                "solve.html",
                error=None,
                cipher_data=c_text,
                remaining_seconds=remaining,
            )

        return render_template(
            "solve.html",
            error=None,
            cipher_data=data,
            remaining_seconds=None,
        )
    except Exception:
        return render_template(
            "solve.html",
            error="Geçersiz veya bozuk doğrulama bağlantısı.",
            cipher_data=None,
            remaining_seconds=None,
        )


@app.route("/cozumle", methods=["GET", "POST"])
def manuel_cozumle():
    decrypted_result = None
    status_error = None
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
                        status_error = "Girilen şifreli paketin 4 dakikalık geçerlilik süresi dolmuştur."
                    else:
                        decrypted_result = decrypt(c_text)
                        if decrypted_result is None:
                            status_error = "Şifreli metin çözümlenemedi. Formatı kontrol edin."
                else:
                    decrypted_result = decrypt(cipher_input)
                    if decrypted_result is None:
                        status_error = "Şifreli metin çözümlenemedi. Formatı kontrol edin."
            except Exception:
                status_error = "Çözümleme sırasında bir hata oluştu."
        else:
            status_error = "Lütfen çözümlenecek şifreli metni girin."

    return render_template(
        "manuel_solve.html",
        decrypted_result=decrypted_result,
        status_error=status_error,
        cipher_input=cipher_input,
    )


if __name__ == "__main__":
    app.run(debug=True)
