import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد مفتاح API وموديلات Groq
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def extract_content(file_storage):
    """استخراج النص من PDF مع معالجة بسيطة للفراغات"""
    text = ""
    try:
        file_storage.seek(0)
        with pdfplumber.open(io.BytesIO(file_storage.read())) as pdf:
            # معالجة أول 15 صفحة لضمان كفاءة الذاكرة
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content: 
                    text += content + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """توليد تقرير أكاديمي شامل (6000 توكن)"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {
                    "role": "system", 
                    "content": "أنت بروفيسور أكاديمي خبير. اكتب بحثاً مفصلاً باللغة العربية الفصحى. استخدم تنسيق Markdown (عناوين، جداول، نقاط). حافظ على رصانة الأسلوب الأكاديمي."
                },
                {"role": "user", "content": f"اكتب تقريراً أكاديمياً موسعاً عن الموضوع التالي: {prompt}"}
            ],
            temperature=0.6,
            max_tokens=6000
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e: 
        return jsonify({'report': f"خطأ في السيرفر: {str(e)}"}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    """تلخيص الملازم بأسلوب الشرح المفصل وليس مجرد نقاط"""
    try:
        raw_text = extract_content(request.files['file'])
        if not raw_text:
            return jsonify({'summary': "لم يتم العثور على نص في الملف"}), 400

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {
                    "role": "system", 
                    "content": """أنت خبير في المناهج الدراسية. المطلوب منك تقديم 'شرح تلخيصي وافٍ'. 
                    اشرح المفاهيم الموجودة في النص بأسلوب تعليمي سلس. 
                    - استخدم الفقرات المترابطة.
                    - إذا ذكرت مصطلحاً علمياً بالعربي، ضع بجانبه ترجمته بالإنجليزية بين قوسين (English Term).
                    - اجعل الشرح مفصلاً وكأنك تشرح لطالب، وليس مجرد ملخص قصير."""
                },
                {"role": "user", "content": f"قدم شرحاً تلخيصياً مفصلاً للنص التالي:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e: 
        return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    """توليد أسئلة MCQ بنظام ثنائي اللغة (عربي - إنجليزي)"""
    try:
        raw_text = extract_content(request.files['file'])
        if not raw_text:
            return jsonify({'error': "الملف فارغ أو غير مدعوم"}), 400

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {
                    "role": "system", 
                    "content": """أنت مصمم اختبارات دولية. قم بإنشاء 10 أسئلة اختيار من متعدد (MCQ) من النص.
                    يجب الالتزام الصارم بالتنسيق التالي لكل سؤال لضمان الوضوح:
                    
                    السؤال: [نص السؤال بالعربية] / [Question in English]
                    A) [الخيار بالعربي] / [Option in English]
                    B) [الخيار بالعربي] / [Option in English]
                    C) [الخيار بالعربي] / [Option in English]
                    D) [الخيار بالعربي] / [Option in English]
                    ---
                    الإجابة الصحيحة: [الحرف فقط]
                    
                    تأكد من فصل الأسطر بشكل جيد لكي لا تتداخل الكلمات العربية مع الإنجليزية."""
                },
                {"role": "user", "content": f"أنشئ الأسئلة المترجمة بناءً على هذا النص:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e: 
        return jsonify({'error': str(e)}), 500

# لضمان التوافق مع Vercel و Python AnyWhere
application = app
if __name__ == "__main__":
    app.run(debug=True)
