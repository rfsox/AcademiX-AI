import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# جلب المفتاح - تأكد من إضافته في Vercel Dashboard
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

def extract_text(file):
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # نحدد أول 15 صفحة لضمان السرعة وعدم الكراش
            for page in pdf.pages[:15]:
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
        if not raw_text: return jsonify({'error': "لم يتم العثور على نص"}), 400

        # استخدمنا 3.1-8b لأنه طلقة بالسرعة ويمنع خطأ 500
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": """أنت خبير أسئلة. أنشئ أسئلة MCQ شاملة.
                التنسيق الصارم لمنع التداخل:
                1. السؤال بالإنجليزية أولاً (EN).
                2. السؤال بالعربية ثانياً (AR).
                3. الخيارات: A, B, C, D بالإنجليزية وتحتها ترجمتها بالعربية.
                4. الجواب الصحيح في النهاية.
                استخدم خطوطاً تفصل بين الأسئلة."""},
                {"role": "user", "content": f"استخرج أسئلة كثيرة من هذا المنهج:\n\n{raw_text[:10000]}"}
            ],
            max_tokens=4000, # تقليلها قليلاً لضمان عدم حدوث Timeout
            temperature=0.3
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_text(request.files['file'])
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "لخص المنهج: اكتب الفقرة بالإنجليزية أولاً ثم ترجمتها العربية تحتها مباشرة."},
                {"role": "user", "content": f"لخص بدقة:\n\n{raw_text[:10000]}"}
            ],
            max_tokens=4000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': str(e)}), 500
