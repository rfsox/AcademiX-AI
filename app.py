import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد مفتاح API الخاص بـ Groq
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# الموديلات المستخدمة
MODEL_ACADEMIC = "llama-3.3-70b-versatile" # للتقارير والتلخيص العميق
MODEL_FAST = "llama-3.1-8b-instant"       # للـ MCQ لضمان السرعة وعدم الكراش

def extract_content(file_storage):
    """دالة لاستخراج النص من ملف PDF بدقة عالية"""
    text = ""
    try:
        file_storage.seek(0)
        with pdfplumber.open(io.BytesIO(file_storage.read())) as pdf:
            # يقرأ أول 20 صفحة لضمان عدم تجاوز حجم الذاكرة
            for page in pdf.pages[:20]:
                content = page.extract_text()
                if content:
                    text += content + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """توليد تقرير أكاديمي طويل (6000 توكن)"""
    try:
        data = request.get_json()
        topic = data.get('prompt')
        
        completion = client.chat.completions.create(
            model=MODEL_ACADEMIC,
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي. اكتب تقريراً مفصلاً جداً باللغة العربية مع مصطلحات إنجليزية. استخدم تنسيق Markdown."},
                {"role": "user", "content": f"اكتب بحثاً شاملاً عن: {topic}"}
            ],
            temperature=0.6,
            max_tokens=6000
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': str(e)}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    """تلخيص شرح مفصل ثنائي اللغة"""
    try:
        raw_text = extract_content(request.files['file'])
        if not raw_text:
            return jsonify({'summary': "لم يتم العثور على نص في الملف"}), 400

        completion = client.chat.completions.create(
            model=MODEL_ACADEMIC,
            messages=[
                {"role": "system", "content": """أنت خبير تلخيص. قدم شرحاً تلخيصياً وافياً.
                القواعد:
                1. شرح المفاهيم بالعربي مع كتابة المصطلحات بالإنجليزية بين قوسين.
                2. تلخيص الأفكار على شكل فقرات مترابطة وليس نقاط فقط.
                3. الحفاظ على المنهج العلمي للملف."""},
                {"role": "user", "content": f"اشرح ولخص هذا النص بأسلوب أكاديمي مترجم:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=5000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    """توليد أسئلة MCQ مترجمة (نظام دفعات لضمان عدم الكراش)"""
    try:
        raw_text = extract_content(request.files['file'])
        if not raw_text:
            return jsonify({'error': "الملف فارغ"}), 400

        # نستخدم الموديل السريع هنا لتجنب 500 Internal Server Error في Vercel
        completion = client.chat.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": """أنت محترف صياغة أسئلة امتحانية. 
                استخرج 15 سؤال MCQ دقيق من المنهج.
                التنسيق الإلزامي لكل سؤال:
                EN: [Question text in English]
                AR: [ترجمة السؤال بالعربية]
                A) [Option EN] / [الترجمة بالعربية]
                B) [Option EN] / [الترجمة بالعربية]
                C) [Option EN] / [الترجمة بالعربية]
                D) [Option EN] / [الترجمة بالعربية]
                Answer: [Correct Option Letter]
                --------------------------------------"""},
                {"role": "user", "content": f"صمم 15 سؤالاً مترجماً من هذا النص:\n\n{raw_text[:8000]}"}
            ],
            temperature=0.3,
            max_tokens=3500
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        print(f"MCQ Error: {e}")
        return jsonify({'error': "حدث خطأ أثناء التوليد، حاول مرة أخرى"}), 500

if __name__ == '__main__':
    app.run(debug=True)
