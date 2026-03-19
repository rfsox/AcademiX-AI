import os
import io
import re
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد مفتاح API من البيئة
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def extract_content(file_storage):
    extracted_text = ""
    try:
        file_storage.seek(0)
        file_bytes = file_storage.read()
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content: extracted_text += content + "\n"
    except: pass
    return extracted_text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": "أنت بروفيسور أكاديمي خبير. اكتب بأسلوب رصين وباللغة العربية الفصحى. اجعل التنسيق متوافقاً مع القراءة من اليمين لليسار (RTL) بشكل دقيق جداً."},
                {"role": "user", "content": f"اكتب بحثاً أكاديمياً مفصلاً حول: {data.get('prompt')}"}
            ],
            temperature=0.6,
            max_tokens=6000  # التعديل لـ 6000 توكن [cite: 250]
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e: return jsonify({'report': str(e)}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "لخص النص التالي بأسلوب نقاط أكاديمية باللغة العربية. تأكد من سلامة ترتيب الجمل والكلمات العربية."},
                {"role": "user", "content": f"Analyze:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e: return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "أنشئ 10 أسئلة MCQ بناءً على النص. اكتب السؤال بالعربي ثم الإنجليزي. حافظ على ترتيب الكلمات العربية من اليمين لليسار دون تداخل."},
                {"role": "user", "content": f"Generate Questions:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e: return jsonify({'error': str(e)}), 500

application = app
