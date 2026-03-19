import os
import io
import re
import base64
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد العميل مع معالجة خطأ غياب المفتاح
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None

# الموديلات
MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"
MODEL_VISION = "llama-3.2-11b-vision-preview"

def clean_text_for_ai(text):
    if not text: return ""
    # تنظيف النصوص مع دعم العربية والإنجليزية والترقيم الأكاديمي
    cleaned = re.sub(r'[^\w\s\.\!\?\u0600-\u06FF\-\:\(\)\[\]]', ' ', text)
    return " ".join(cleaned.split())

def extract_content(file_storage):
    extracted_text = ""
    try:
        # قراءة الملف كـ Bytes مرة واحدة لتوفير الذاكرة في Vercel
        file_bytes = file_storage.read()
        if not file_bytes: return ""
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # تقليل عدد الصفحات لـ 10 لضمان عدم تجاوز الـ 10 ثوانٍ في Vercel Free
            for page in pdf.pages[:10]:
                content = page.extract_text()
                if content:
                    extracted_text += content + "\n"
    except Exception as e:
        print(f"Extraction Error: {e}")
    return clean_text_for_ai(extracted_text)

@app.route('/')
def index():
    return render_template('index.html')

# 1. توليد التقارير
@app.route('/generate', methods=['POST'])
def generate():
    if not client: return jsonify({'error': 'API Key is missing'}), 500
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt: return jsonify({'report': 'الرجاء إدخال الموضوع'})

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": "أنت بروفيسور أكاديمي. اكتب بحثاً مفصلاً بالعربية بتنسيق Markdown مع جداول ومراجع."},
                {"role": "user", "content": f"اكتب بحثاً حول: {prompt}"}
            ],
            temperature=0.5,
            max_tokens=2500 # تقليل الـ Tokens قليلاً لتجنب الـ Timeout في Vercel
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. تلخيص الملفات
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files: return jsonify({'error': 'الملف مفقود'}), 400
        raw_text = extract_content(request.files['file'])
        if not raw_text: return jsonify({'error': 'لا يمكن قراءة الملف'})

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "قدم ملخصاً تنفيذياً بالإنجليزية ثم شرحاً مفصلاً بالعربية بالنقاط."},
                {"role": "user", "content": f"Analyze: {raw_text[:8000]}"} # حجم نص آمن
            ]
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. توليد الأسئلة MCQ
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files: return jsonify({'error': 'ارفع ملف أولاً'}), 400
        raw_text = extract_content(request.files['file'])
        
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "Generate 10 MCQs in English and Arabic with correct answers at the end."},
                {"role": "user", "content": f"Text: {raw_text[:8000]}"}
            ]
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. محرك الرؤية (Vision)
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        if 'image' not in request.files: return jsonify({'error': 'الصورة مفقودة'}), 400
        image_file = request.files['image']
        # ضغط بسيط للصورة قبل الإرسال لتسريع العملية
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        completion = client.chat.completions.create(
            model=MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "حل هذه المسألة الأكاديمية بالتفصيل بالعربية."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )
        return jsonify({'solution': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# تصحيح التعريف لـ Vercel
app = app
