import os
import io
import base64
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# إعداد مفتاح API
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# دالة استخراج النص من PDF
def extract_pdf(file):
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages[:10]: # معالجة أول 10 صفحات فقط للسرعة
                text += page.extract_text() + "\n"
    except: pass
    return text

@app.route('/')
def index():
    return render_template('index.html')

# ميزة 1: توليد التقارير
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"اكتب تقريراً أكاديمياً مفصلاً بالعربية حول: {prompt}"}]
    )
    return jsonify({'report': completion.choices[0].message.content})

# ميزة 2: حل الصور (Vision)
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files: return jsonify({'error': 'No image'}), 400
    img = request.files['image']
    base64_image = base64.b64encode(img.read()).decode('utf-8')
    
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "حل المسألة الموجودة في الصورة بالتفصيل بالعربية"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }]
    )
    return jsonify({'solution': completion.choices[0].message.content})

# ميزة 3: تلخيص PDF
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    file = request.files['file']
    text = extract_pdf(file)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"لخص هذا النص بالعربية والإنجليزية:\n{text[:8000]}"}]
    )
    return jsonify({'summary': completion.choices[0].message.content})

application = app
