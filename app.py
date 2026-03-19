import os
import io
import re
import base64
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# تعريف التطبيق وتحديد مسار المجلدات الثابتة لضمان عدم تخبط التصميم
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد العميل
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# الموديلات
MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"
MODEL_VISION = "llama-3.2-11b-vision-preview"

def clean_text_for_ai(text):
    if not text: return ""
    cleaned = re.sub(r'[^\w\s\.\!\?\u0600-\u06FF]', ' ', text)
    return " ".join(cleaned.split())

def extract_content(file_storage):
    extracted_text = ""
    try:
        file_storage.seek(0)
        file_bytes = file_storage.read()
        if not file_bytes: return ""
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # تقليل عدد الصفحات لـ 15 لضمان عدم تجاوز الـ Timeout في Vercel مجاني
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content:
                    extracted_text += content + "\n"
    except Exception as e:
        print(f"Extraction Error: {e}")
    return clean_text_for_ai(extracted_text)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt: return jsonify({'report': 'يرجى إدخال الموضوع'})

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": "أنت بروفيسور أكاديمي. اكتب باللغة العربية مباشرة وبدون مقدمات."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000 # تقليل التوكنز قليلاً لتسريع الرد
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ: {str(e)}"}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files: return jsonify({'summary': 'الملف مفقود'}), 400
        raw_text = extract_content(request.files['file'])
        if not raw_text: return jsonify({'summary': 'لم أتمكن من استخراج نص.'})

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "تلخيص احترافي: فقرة إنجليزية متبوعة بترجمة عربية."},
                {"role": "user", "content": f"Analyze:\n\n{raw_text[:10000]}"}
            ],
            temperature=0.3
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files: return jsonify({'error': 'ارفع ملف أولاً'}), 400
        raw_text = extract_content(request.files['file'])

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "Generate MCQs in English and Arabic. Markdown only."},
                {"role": "user", "content": f"Create questions from:\n\n{raw_text[:10000]}"}
            ],
            temperature=0.5
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        if 'image' not in request.files: return jsonify({'error': 'الصورة مفقودة'}), 400
        
        image_file = request.files['image']
        # تأكد من ضغط الصورة إذا كانت كبيرة جداً لتجنب خطأ Payload Too Large
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        completion = client.chat.completions.create(
            model=MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "حل هذا السؤال الأكاديمي بالتفصيل وبالعربية."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1500
        )
        return jsonify({'solution': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f"خطأ الرؤية: {str(e)}"}), 500

# السطر الذهبي لـ Vercel
app.debug = False
application = app

if __name__ == '__main__':
    app.run()
