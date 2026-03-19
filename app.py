import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# جلب المفتاح - تأكد من وضعه في Vercel Dashboard
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# استخدام أسرع موديل لمنع الـ Timeout (الخطأ 500)
MODEL_FAST = "llama-3.1-8b-instant"

def extract_text(file):
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # نكتفي بأول 5 صفحات لضمان سرعة خرافية
            for page in pdf.pages[:5]:
                content = page.extract_text()
                if content: text += content + "\n"
    except: pass
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_text(request.files['file'])
        if not raw_text: 
            return jsonify({'error': "الملف فارغ أو غير مدعوم"}), 400

        # نطلب 5 أسئلة فقط لضمان وصول الرد في أقل من 3 ثوانٍ
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": """أنت خبير أسئلة سريع. أنشئ 5 أسئلة MCQ مترجمة.
                التنسيق:
                EN: Question?
                AR: السؤال بالعربي؟
                A) Option EN / الترجمة
                Answer: [الخيار]"""},
                {"role": "user", "content": f"أنشئ 5 أسئلة من هذا النص:\n\n{raw_text[:5000]}"}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': "السيرفر مشغول، حاول مرة أخرى"}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_text(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "اشرح النص باختصار وترجمة واضحة."},
                {"role": "user", "content": f"لخص هذا النص:\n\n{raw_text[:5000]}"}
            ],
            max_tokens=1000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except:
        return jsonify({'summary': "حدث خطأ في التلخيص"}), 500

if __name__ == '__main__':
    app.run(debug=True)
