import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# استخدام الموديل الأقوى لضمان عدم ترك أي معلومة في المنهج
MODEL_NAME = "llama-3.3-70b-versatile"

def extract_all_text(file):
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # يقرأ حتى 40 صفحة لضمان تغطية المنهج كاملاً
            for page in pdf.pages[:40]:
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
                {"role": "system", "content": """أنت خبير أكاديمي. قدم ملخصاً شاملاً للمنهج.
                يجب أن يكون نظام التلخيص كالتالي:
                1. الفقرة باللغة الإنجليزية أولاً بالكامل.
                2. ثم ترجمتها العربية الدقيقة تحتها مباشرة.
                استخدم العناوين الواضحة (Heading) لكل قسم."""},
                {"role": "user", "content": f"لخص هذا المنهج بدقة عالية ولا تترك تفاصيل:\n\n{raw_text[:15000]}"}
            ],
            max_tokens=7000,
            temperature=0.5
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"Error: {str(e)}"}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_all_text(request.files['file'])
        # نطلب عدد كبير من الأسئلة لتغطية كل المنهج
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": """أنت خبير في وضع الأسئلة الوزارية. 
                استخرج بنك أسئلة ضخم (أكبر عدد ممكن) يغطي كل تفاصيل النص المرفق.
                نظام التنسيق الإلزامي لمنع التداخل:
                - السؤال بالإنجليزية أولاً.
                - السؤال بالعربية ثانياً.
                - الخيارات: (A, B, C, D) بالإنجليزية وتحتها ترجمتها بالعربية.
                - ضع مفتاح الحل في النهاية.
                ملاحظة: لا تترك أي ورقة في المنهج دون سؤال."""},
                {"role": "user", "content": f"أنشئ أسئلة MCQ شاملة جداً لهذا المنهج:\n\n{raw_text[:18000]}"}
            ],
            max_tokens=7000,
            temperature=0.3
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
