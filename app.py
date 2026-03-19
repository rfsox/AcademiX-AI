import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# مكتبات معالجة النص العربي لضمان القراءة الصحيحة
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_TOOLS = True
except ImportError:
    HAS_ARABIC_TOOLS = False

app = Flask(__name__)
CORS(app)

# إعداد العميل
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

def fix_extracted_text(text):
    """تصحيح ترتيب الحروف العربية المستخرجة من PDF"""
    if not text: return ""
    if HAS_ARABIC_TOOLS:
        # إصلاح الحروف المقطعة والمعكوسة التي تظهر في بعض ملفات الـ PDF
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير (8000 توكن + تفصيل أكاديمي) ---
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
                        "أنت بروفيسور خبير. قدم تقريراً طويلاً جداً ومفصلاً وشاملاً. "
                        "يجب أن يكون التقرير غنياً بالمعلومات مع عناوين فرعية ومراجع. "
                        "استخدم لغة أكاديمية رصينة ولا تتوقف حتى تنهي كافة جوانب الموضوع."
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

# --- 2. تلخيص PDF (حل مشكلة الانقطاع + ترجمة احترافية) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        extracted_text = ""
        
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            # زيادة عدد الصفحات المعالجة لضمان شمولية التلخيص
            for page in pdf.pages[:50]: 
                text = page.extract_text()
                if text:
                    extracted_text += fix_extracted_text(text) + "\n"

        if not extracted_text.strip():
            return jsonify({'summary': 'الملف لا يحتوي على نص قابل للقراءة.'})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an expert academic summarizer. Your goal is to provide a MASSIVE, DETAILED summary. "
                        "For each section of the document, provide: "
                        "1. Detailed English explanation. "
                        "2. Immediate accurate Arabic translation. "
                        "Keep the flow continuous and do not cut the text short. Use 8000 tokens fully if needed."
                    )
                },
                {"role": "user", "content": f"Analyze this text in depth (English & Arabic):\n\n{extracted_text[:30000]}"}
            ],
            temperature=0.5,
            max_tokens=8000 
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# --- 3. مصنع الأسئلة MCQ (جديد: رفع ملف + ترجمة مقابلة + 8000 توكن) ---
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'يرجى إرفاق ملف لإنشاء الأسئلة'}), 400
        
        file = request.files['file']
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages[:30]: # قراءة نص كافٍ لتوليد أسئلة كثيرة
                text = page.extract_text()
                if text:
                    extracted_text += fix_extracted_text(text) + "\n"

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "أنت خبير في وضع المناهج والأسئلة الامتحانية. "
                        "قم بتوليد أكبر عدد ممكن من أسئلة الاختيار من متعدد (MCQ). "
                        "نظام العمل: اكتب السؤال بالإنجليزية وتحته مباشرة الترجمة العربية. "
                        "الخيارات (A, B, C, D) يجب أن تكون مترجمة أيضاً. "
                        " ضع الاجابه الصحسحه تحت كل سؤال ومترجمه. "
                        "استخدم تنسيق Markdown لجعل الأسئلة سهلة القراءة والطباعة."
                    )
                },
                {"role": "user", "content": f"Generate a huge bank of MCQs from this text:\n\n{extracted_text[:25000]}"}
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
