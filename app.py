import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def extract_content(file):
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages[:20]: # يقرأ حتى 20 صفحة
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
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي. لخص النص بأسلوب فقرات: الإنجليزية أولاً ثم ترجمتها العربية تحتها مباشرة. استخدم 7000 توكن للشرح الوافي."},
                {"role": "user", "content": f"لخص هذا المنهج بدقة:\n\n{raw_text[:15000]}"}
            ],
            max_tokens=7000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e: return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # سريع جداً لمنع الـ Timeout
            messages=[
                {"role": "system", "content": """أنشئ أسئلة MCQ شاملة لكل المنهج. 
                التنسيق: 
                EN: [Question]
                AR: [السؤال]
                A) [Option EN] / [الترجمة العربية]
                Answer: [Correct Option]"""},
                {"role": "user", "content": f"أنشئ أسئلة من هذا النص:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=7000
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e: return jsonify({'error': str(e)}), 500
