import os
import io
import re
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد العميل - تأكد من وجود المفتاح في Environment Variables على فيرسل
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# الموديلات المستقرة
MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def clean_text(text):
    if not text: return ""
    # تنظيف النص مع الحفاظ على الحروف العربية والإنجليزية والترقيم
    cleaned = re.sub(r'[^\w\s\.\!\?\u0600-\u06FF\-\:\(\)]', ' ', text)
    return " ".join(cleaned.split())

def extract_content(file_storage):
    extracted_text = ""
    try:
        file_storage.seek(0)
        file_bytes = file_storage.read()
        if not file_bytes: return ""
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # معالجة أول 15 صفحة فقط لضمان سرعة الاستجابة
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content:
                    extracted_text += content + "\n"
    except Exception as e:
        print(f"Error: {e}")
    return clean_text(extracted_text)

@app.route('/')
def index():
    return render_template('index.html')

# 1. محرك توليد التقارير
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt: return jsonify({'report': 'يرجى إدخال الموضوع'})

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": "أنت بروفيسور أكاديمي خبير. اكتب تقريراً مفصلاً باللغة العربية بتنسيق Markdown يتضمن مقدمة، محاور، جدول بيانات، ومراجع."},
                {"role": "user", "content": f"اكتب بحثاً أكاديمياً حول: {prompt}"}
            ],
            temperature=0.6,
            max_tokens=3000 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ: {str(e)}"}), 500

# 2. محرك التلخيص
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files: return jsonify({'summary': 'الملف مفقود'}), 400
        raw_text = extract_content(request.files['file'])
        if not raw_text: return jsonify({'summary': 'نص غير قابل للقراءة'})

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "لخص النص التالي: ابدأ بفقرة إنجليزية ثم شرح مفصل بالنقاط بالعربية."},
                {"role": "user", "content": f"Analyze this text:\n\n{raw_text[:10000]}"}
            ]
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': str(e)}), 500

# 3. محرك الأسئلة MCQ
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files: return jsonify({'error': 'ارفع ملف أولاً'}), 400
        raw_text = extract_content(request.files['file'])

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "أنشئ 10 أسئلة MCQ بالإنجليزية والعربية مع الإجابات الصحيحة في النهاية."},
                {"role": "user", "content": f"Text:\n\n{raw_text[:10000]}"}
            ]
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# توافق مع Vercel
application = app

if __name__ == '__main__':
    app.run(debug=False)
