import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# 1. إعداد التطبيق
app = Flask(__name__)
CORS(app)

# 2. إعداد العميل (تأكد من وضع المفتاح في Vercel Environment Variables)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# الموديلات المستخدمة:
# 70b للتقارير المعقدة التي تحتاج ذكاء عالي
# 8b للملخصات والأسئلة لضمان استجابة سريعة جداً تمنع خطأ 500
MODEL_DEEP = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def extract_pdf_content(file):
    """استخراج النص بذكاء مع تحديد سقف لعدد الصفحات لضمان استقرار السيرفر"""
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # نكتفي بأول 20 صفحة لضمان بقاء وقت المعالجة تحت 10 ثوانٍ (قيد Vercel)
            for page in pdf.pages[:20]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass
    return text

@app.route('/')
def index():
    return render_template('index.html')

# --- مسار توليد التقارير (Prompt Based) ---
@app.route('/generate', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        
        response = client.chat.completions.create(
            model=MODEL_DEEP,
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي محترف. اكتب تقريراً مفصلاً ومنظماً بالعربية مع استخدام المصطلحات الإنجليزية الضرورية."},
                {"role": "user", "content": f"اكتب بحثاً أكاديمياً معمقاً عن: {user_prompt}"}
            ],
            max_tokens=1000,
            temperature=0.5
        )
        return jsonify({'report': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- مسار تلخيص الـ PDF (File Based) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        raw_text = extract_pdf_content(request.files['file'])
        if not raw_text:
            return jsonify({'summary': "تعذر استخراج نص من الملف. تأكد أنه ليس ملف صور."}), 400

        # نستخدم الموديل السريع هنا لضمان عدم حدوث Timeout
        response = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": """لخص النص بأسلوب أكاديمي. 
                التنسيق المطلوب: 
                - اكتب الفقرة بالإنجليزية أولاً.
                - أتبعها مباشرة بالترجمة العربية الدقيقة.
                اجعل الشرح وافياً بحدود 800 توكن."""},
                {"role": "user", "content": f"لخص هذا المنهج:\n\n{raw_text[:10000]}"}
            ],
            max_tokens=1000
        )
        return jsonify({'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"حدث خطأ: {str(e)}"}), 500

# --- مسار توليد الأسئلة (File Based) ---
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        raw_text = extract_pdf_content(request.files['file'])
        
        response = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": """قم بإنشاء بنك أسئلة MCQ شامل من النص.
                لكل سؤال:
                1. السؤال بالإنجليزية.
                2. السؤال بالعربية.
                3. الخيارات (A, B, C, D) باللغتين.
                4. الإجابة الصحيحة في النهاية.
                اجعل الأسئلة تغطي كافة النقاط الجوهرية."""},
                {"role": "user", "content": f"أنشئ أسئلة من هذا النص:\n\n{raw_text[:10000]}"}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        return jsonify({'questions': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f"خطأ في توليد الأسئلة: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
