import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# إعداد العميل
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

def extract_clean_text(file_storage):
    """استخراج النص من PDF بدون تخريب الترتيب العربي"""
    extracted_text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_storage.read())) as pdf:
            # معالجة أول 40 صفحة لضمان عدم الانقطاع وتغطية المحتوى
            for page in pdf.pages[:40]:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return extracted_text

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير (8000 توكن) ---
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'report': 'يرجى إدخال موضوع البحث'})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "أنت بروفيسور خبير. اكتب بأسلوب أكاديمي رصين. "
                        "يجب أن يكون النص العربي منسقاً وسليماً لغوياً (من اليمين لليسار). "
                        "قدم تقريراً ضخماً ومفصلاً جداً يتجاوز الـ 8000 توكن."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8000 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ: {str(e)}"}), 500

# --- 2. تلخيص PDF (تعديل لتجنب الـ Rate Limit) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        text = extract_clean_text(file)
        
        if not text.strip():
            return jsonify({'summary': 'الملف لا يحتوي على نص قابل للقراءة.'})

        completion = client.chat.completions.create(
            # غيرنا النموذج لنسخة أسرع وأخف استهلاكاً للرصيد المجاني
            model="llama3-8b-8192", 
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an academic summarizer. Provide a thorough summary. "
                        "Format: English section followed by Arabic translation. "
                        "Keep the Arabic natural and correctly aligned."
                    )
                },
                {"role": "user", "content": f"Summarize this text comprehensively:\n\n{text[:15000]}"}
            ],
            temperature=0.5,
            max_tokens=4000 # قللنا لـ 4000 حتى يتقبله السيرفر المجاني وما يرفض الطلب
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        # إذا خلص الرصيد تماماً، تظهر رسالة مفهومة
        if "rate_limit_exceeded" in str(e).lower():
            return jsonify({'summary': "⚠️ انتهت حصتك المجانية من الكلمات لهذا اليوم. يرجى المحاولة بعد ساعة أو غداً."}), 429
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# --- 3. مصنع الأسئلة MCQ (حل مشكلة النص المعكوس) ---
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'يرجى إرفاق ملف'}), 400
        
        text = extract_clean_text(request.files['file'])

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "أنت خبير وضع امتحانات. قم بتوليد أسئلة MCQ كثيرة جداً. "
                        "قاعدة صارمة: اكتب السؤال بالإنجليزية أولاً، ثم ترجمته العربية أسفله مباشرة. "
                        "تأكد أن النص العربي مكتوب بشكل صحيح وسليم (Natural Arabic) وليس حروفاً مقطعة. "
                        "أظهر الخيارات (A, B, C, D) مع ترجمتها، ثم الإجابة الصحيحة مع التوضيح. "
                        "استخدم Markdown والتنسيق التالي:\n"
                        "Q1: [English Question]\nس1: [السؤال بالعربي]\n"
                    )
                },
                {"role": "user", "content": f"Generate a massive MCQ bank from this text:\n\n{text[:25000]}"}
            ],
            temperature=0.6,
            max_tokens=8000 
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

application = app
if __name__ == '__main__':
    app.run(debug=True)
