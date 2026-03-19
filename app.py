import os
import io
import re
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# إعداد العميل
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# الموديلات المعتمدة للاستقرار
MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"

def clean_text_for_ai(text):
    """تنظيف النص من أي رموز غريبة قد تسبب ارتباكاً للموديل"""
    if not text: return ""
    # إزالة الرموز غير الضرورية مع الحفاظ على الحروف العربية والإنجليزية والأرقام
    cleaned = re.sub(r'[^\w\s\.\!\?\u0600-\u06FF]', ' ', text)
    return " ".join(cleaned.split())

def extract_content(file_storage):
    """استخراج النص بذكاء مع تصفير المؤشر"""
    extracted_text = ""
    try:
        file_storage.seek(0)
        with pdfplumber.open(io.BytesIO(file_storage.read())) as pdf:
            # نأخذ أول 30 صفحة لضمان جودة عالية وعدم تشتت الذكاء الاصطناعي
            for page in pdf.pages[:30]:
                content = page.extract_text()
                if content:
                    extracted_text += content + "\n"
    except Exception as e:
        print(f"Extraction Error: {e}")
    return clean_text_for_ai(extracted_text)

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير (تركيز عالي) ---
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt: return jsonify({'report': 'يرجى إدخال الموضوع'})

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": "أنت بروفيسور أكاديمي. اكتب مباشرة باللغة العربية. ممنوع كتابة مقدمات مثل 'حاضر' أو 'إليك التقرير'. ابدأ بالعناوين فوراً وبشكل مفصل جداً."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=6000 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ في السيرفر: {str(e)}"}), 500

# --- 2. تلخيص PDF (حل مشكلة الاعتذار بالإنجليزية) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files: return jsonify({'summary': 'الملف مفقود'}), 400
        
        raw_text = extract_content(request.files['file'])
        if len(raw_text) < 50: return jsonify({'summary': 'تعذر قراءة نص كافٍ من الملف.'})

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "STRICT RULES: \n"
                        "1. START THE SUMMARY IMMEDIATELY.\n"
                        "2. Format: Detailed English paragraph followed by a Professional Arabic translation.\n"
                        "3. NO introductions, NO 'I understand', NO apologies about translation machine.\n"
                        "4. Focus only on the content provided."
                    )
                },
                {"role": "user", "content": f"Text to analyze:\n\n{raw_text[:15000]}"}
            ],
            temperature=0.4,
            max_tokens=4000 
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# --- 3. مصنع الأسئلة MCQ (تنسيق صارم) ---
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files: return jsonify({'error': 'ارفع ملف أولاً'}), 400
        
        raw_text = extract_content(request.files['file'])

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an exam generator. Create a long list of MCQs.\n"
                        "Each question must be in English, followed by its Arabic translation.\n"
                        "Choices A, B, C, D must be translated.\n"
                        "Highlight the correct answer at the end of each question.\n"
                        "USE MARKDOWN. DO NOT CHAT WITH THE USER."
                    )
                },
                {"role": "user", "content": f"Create MCQs from this:\n\n{raw_text[:15000]}"}
            ],
            temperature=0.5,
            max_tokens=5000 
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

application = app
if __name__ == '__main__':
    app.run(debug=True)
