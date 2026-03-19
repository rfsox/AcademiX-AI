import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# جلب المفتاح من إعدادات Vercel - تأكد من إضافته هناك
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# الموديلات المستقرة
MODEL_QUICK = "llama-3.1-8b-instant"   # سريع جداً للأسئلة والملخص لمنع التوقف
MODEL_POWER = "llama-3.3-70b-versatile" # قوي جداً للتقارير الطويلة

def extract_text(file):
    """دالة استخراج النص من الـ PDF مع تحديد عدد الصفحات للسرعة"""
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # نكتفي بأول 15 صفحة لضمان بقاء المعالجة ضمن وقت Vercel المسموح
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content: text += content + "\n"
    except: pass
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_report():
    """توليد تقرير أكاديمي مفصل"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        completion = client.chat.completions.create(
            model=MODEL_POWER,
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي. اكتب تقريراً مفصلاً جداً باللغة العربية مع المصطلحات الإنجليزية."},
                {"role": "user", "content": f"اكتب بحثاً شاملاً عن: {prompt}"}
            ],
            max_tokens=800, # التوكن المطلوب للاستقرار
            temperature=0.6
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': str(e)}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    """ملخص وتنظيم لغات (إنجليزي أولاً ثم عربي)"""
    try:
        text = extract_text(request.files['file'])
        if not text: return jsonify({'summary': "لم يتم العثور على نص"}), 400

        completion = client.chat.completions.create(
            model=MODEL_QUICK,
            messages=[
                {"role": "system", "content": """أنت خبير تلخيص. 
                نظم الإجابة كالتالي: 
                - الفقرة باللغة الإنجليزية أولاً بالكامل.
                - الترجمة العربية تحتها مباشرة.
                استخدم توكن 800 للشرح."""},
                {"role": "user", "content": f"لخص هذا المنهج:\n\n{text[:8000]}"}
            ],
            max_tokens=800
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    """توليد أسئلة MCQ مرتبة ومنظمة"""
    try:
        text = extract_text(request.files['file'])
        if not text: return jsonify({'error': "الملف فارغ"}), 400

        completion = client.chat.completions.create(
            model=MODEL_QUICK,
            messages=[
                {"role": "system", "content": """أنشئ أسئلة MCQ مترجمة.
                التنسيق: 
                1. السؤال بالإنجليزية.
                2. السؤال بالعربية.
                3. الخيارات (A, B, C, D) باللغتين.
                4. الجواب الصحيح."""},
                {"role": "user", "content": f"أنشئ أسئلة من المنهج:\n\n{text[:8000]}"}
            ],
            max_tokens=800,
            temperature=0.3
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
