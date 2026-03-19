import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def extract_content(file_storage):
    text = ""
    try:
        file_storage.seek(0)
        with pdfplumber.open(io.BytesIO(file_storage.read())) as pdf:
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content: text += content + "\n"
    except: pass
    return text

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
                {"role": "system", "content": "أنت خبير أكاديمي. اكتب بأسلوب التقرير المفصل. استخدم لغة عربية رصينة وتنسيق Markdown واضح."},
                {"role": "user", "content": f"اكتب تقريراً شاملاً عن: {data.get('prompt')}"}
            ],
            temperature=0.6,
            max_tokens=6000
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e: return jsonify({'report': str(e)}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": "أنت خبير تلخيص. المطلوب: تقديم شرح تلخيصي وافٍ ومفصل للنص (وليس مجرد رؤوس أقلام أو خيارات). اشرح الأفكار الرئيسية بأسلوب فقرات مترابطة باللغة العربية."},
                {"role": "user", "content": f"لخص هذا النص شرحاً وافياً:\n\n{raw_text[:12000]}"}
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
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": """أنشئ 10 أسئلة MCQ احترافية. 
                يجب الالتزام بالتنسيق التالي لكل سؤال:
                1. السؤال بالعربية وتحته الترجمة الإنجليزية.
                2. الاختيارات (A, B, C, D) بالعربية وتحتها الترجمة الإنجليزية لكل خيار.
                3. ذكر الإجابة الصحيحة في النهاية.
                تأكد من فصل الأسطر لكي لا تتداخل اللغة العربية مع الإنجليزية."""},
                {"role": "user", "content": f"أنشئ الأسئلة من هذا النص:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e: return jsonify({'error': str(e)}), 500

application = app
