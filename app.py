import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# إعداد التطبيق
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# جلب المفتاح من إعدادات Vercel
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# استخدام موديل 8B لأنه الأسرع عالمياً ويمنع خطأ الـ 500
MODEL_FAST = "llama-3.1-8b-instant" 
MODEL_DEEP = "llama-3.3-70b-versatile"

def extract_pdf_text(file):
    """استخراج النص بسرعة من أول 10 صفحات فقط لضمان استقرار السيرفر"""
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages[:10]:
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
        prompt = data.get('prompt')
        completion = client.chat.completions.create(
            model=MODEL_DEEP,
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي. اكتب تقريراً مفصلاً ومنظماً بالعربية."},
                {"role": "user", "content": f"اكتب بحثاً عن: {prompt}"}
            ],
            max_tokens=3000
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': str(e)}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_pdf_text(request.files['file'])
        if not raw_text: return jsonify({'summary': "تعذر قراءة الملف"}), 400
        
        completion = client.chat.completions.create(
            model=MODEL_DEEP,
            messages=[
                {"role": "system", "content": "لخص النص بأسلوب شرح أكاديمي مفصل (عربي/إنجليزي)."},
                {"role": "user", "content": f"اشرح النص التالي:\n\n{raw_text[:7000]}"}
            ],
            max_tokens=2500
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_pdf_text(request.files['file'])
        if not raw_text: return jsonify({'error': "الملف فارغ"}), 400

        # السر هنا: طلب 10 أسئلة فقط لضمان الرد في أقل من 5 ثوانٍ
        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": """أنشئ 10 أسئلة MCQ بدقة من المنهج.
                التنسيق:
                EN: Question?
                AR: ترجمة السؤال؟
                A) Option / الترجمة
                B) Option / الترجمة
                C) Option / الترجمة
                D) Option / الترجمة
                Answer: [الخيار الصحيح]"""},
                {"role": "user", "content": f"أنشئ 10 أسئلة مترجمة من هذا النص:\n\n{raw_text[:7000]}"}
            ],
            temperature=0.2,
            max_tokens=2500
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
