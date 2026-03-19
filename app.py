import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# جلب المفتاح من إعدادات Vercel
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# استخدام الموديل الأقوى لضمان عدم ترك أي تفصيلة في المنهج
MODEL_NAME = "llama-3.3-70b-versatile"

def extract_all_text(file):
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # يقرأ حتى 30 صفحة لضمان شمولية المنهج
            for page in pdf.pages[:30]:
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
        raw_text = extract_all_text(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": """أنت خبير أكاديمي رفيع المستوى. 
                المطلوب: شرح وتلخيص المنهج كاملاً بـ 7000 توكن.
                نظام التنسيق الإلزامي:
                1. الفقرة باللغة الإنجليزية أولاً (English Text).
                2. الترجمة العربية الوافية تحتها مباشرة (Arabic Translation).
                3. استخدم العناوين الكبيرة والمميزة. لا تترك أي موضوع دون شرح."""},
                {"role": "user", "content": f"لخص هذا المنهج بدقة متناهية:\n\n{raw_text[:18000]}"}
            ],
            max_tokens=7000,
            temperature=0.4
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"Error: {str(e)}"}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_all_text(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": """أنت واضع أسئلة امتحانية محترف.
                المطلوب: توليد أكبر عدد ممكن من الأسئلة (MCQ) لتغطية المنهج بنسبة 100%.
                نظام التنسيق (هام جداً):
                - السؤال بالإنجليزية.
                - السؤال بالعربية.
                - الخيارات (A, B, C, D) بالإنجليزية وتحتها ترجمتها بالعربية.
                - مفتاح الحل في النهاية.
                افصل بين كل سؤال والآخر بخط واضح."""},
                {"role": "user", "content": f"أنشئ بنك أسئلة شامل لهذا المنهج:\n\n{raw_text[:18000]}"}
            ],
            max_tokens=7000,
            temperature=0.3
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
