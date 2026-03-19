import os
import io
import re
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# إعداد التطبيق
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد عميل GROQ - تأكد من إضافة المفتاح في إعدادات Vercel
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# الموديلات المستخدمة
MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def extract_content(file_storage):
    """وظيفة استخراج النصوص من ملفات PDF بدقة"""
    extracted_text = ""
    try:
        file_storage.seek(0)
        file_bytes = file_storage.read()
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # قراءة أول 15 صفحة لضمان عدم تجاوز حدود الذاكرة
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content:
                    extracted_text += content + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return extracted_text

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """توليد التقارير والبحوث الأكاديمية"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'report': 'الرجاء إدخال موضوع البحث'}), 400

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {
                    "role": "system", 
                    "content": "أنت بروفيسور أكاديمي خبير ومساعد بحث علمي. اكتب بأسلوب رصين وباللغة العربية الفصحى حصراً. استخدم تنسيق Markdown (عناوين، نقاط، جداول). تأكد من أن النص موجه من اليمين لليسار (RTL) ولا تعكس ترتيب الكلمات العربية إطلاقاً."
                },
                {"role": "user", "content": f"اكتب بحثاً أكاديمياً شاملاً ومفصلاً مع مقدمة وفصول وخاتمة حول: {prompt}"}
            ],
            temperature=0.6,
            max_tokens=6000  # السعة المطلوبة 6000 توكن
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"حدث خطأ في السيرفر: {str(e)}"}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    """تلخيص ملفات PDF"""
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم رفع ملف'}), 400
            
        raw_text = extract_content(request.files['file'])
        if not raw_text:
            return jsonify({'summary': 'تعذر استخراج نص من الملف'}), 400

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {
                    "role": "system", 
                    "content": "أنت خبير في تلخيص الأوراق العلمية. لخص النص التالي في نقاط مركزة وباللغة العربية. حافظ على المفاهيم الأساسية والترتيب الصحيح للجمل."
                },
                {"role": "user", "content": f"قم بتلخيص هذا النص بشكل احترافي:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    """توليد أسئلة اختيار من متعدد"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'لم يتم رفع ملف'}), 400

        raw_text = extract_content(request.files['file'])
        
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {
                    "role": "system", 
                    "content": "قم بتوليد 10 أسئلة اختيار من متعدد (MCQ) بناءً على النص. اكتب السؤال بالعربي ثم بالإنجليزي (إن وجد مصطلح). تأكد من أن ترتيب الخيارات والكلمات العربية سليم تماماً من اليمين لليسار."
                },
                {"role": "user", "content": f"أنشئ الأسئلة من هذا النص:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# لضمان العمل على Vercel
application = app
