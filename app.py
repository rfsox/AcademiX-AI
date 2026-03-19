import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# تأكد من وضع المفتاح في إعدادات Vercel
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# استخدام الموديل المستقر والسريع لضمان عدم حدوث Timeout
MODEL_NAME = "llama-3.1-8b-instant"

def extract_clean_text(file):
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # نكتفي بـ 10 صفحات لضمان جودة الاستخراج وسرعة الرد
            for page in pdf.pages[:10]:
                content = page.extract_text()
                if content: text += content + "\n"
    except: pass
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_clean_text(request.files['file'])
        if not raw_text: return jsonify({'summary': "لم يتم العثور على نص قابل للقراءة"}), 400

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": """أنت خبير تلخيص أكاديمي. 
                يجب أن يكون ردك منظماً جداً للفصل بين اللغات:
                - اكتب الفكرة بالإنجليزية في سطر مستقل.
                - اكتب ترجمتها العربية في السطر الذي يليه مباشرة.
                - لا تخلط اللغتين في نفس السطر أبداً.
                - الحد الأقصى للرد هو 800 توكن."""},
                {"role": "user", "content": f"لخص هذا النص بوضوح:\n\n{raw_text[:7000]}"}
            ],
            max_tokens=800,
            temperature=0.5
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"Server Error: {str(e)}"}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_clean_text(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": """أنشئ أسئلة MCQ احترافية.
                نظام التنسيق الإلزامي:
                Question (EN)
                السؤال (AR)
                A) Option (EN) / الخيار (AR)
                Answer: [Correct Option]
                التزم بـ 800 توكن كحد أقصى."""},
                {"role": "user", "content": f"أنشئ أسئلة من المنهج:\n\n{raw_text[:7000]}"}
            ],
            max_tokens=800,
            temperature=0.3
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        topic = data.get('prompt', '')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # للتقرير نستخدم الموديل الأقوى
            messages=[
                {"role": "system", "content": "اكتب تقريراً أكاديمياً مفصلاً بالعربية مع مصطلحات إنجليزية واضحة."},
                {"role": "user", "content": f"اكتب عن: {topic}"}
            ],
            max_tokens=800
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': str(e)}), 500
