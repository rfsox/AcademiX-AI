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
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير (تم زيادة الطول) ---
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
                        "أنت بروفيسور خبير. قدم تقريراً طويلاً جداً ومفصلاً. "
                        "يجب أن يتجاوز التقرير 2000 كلمة مع عناوين واضحة ومراجع أكاديمية."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8000 # زيادة الحد الأقصى للكلمات
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ: {str(e)}"}), 500

# --- 2. تلخيص PDF (تم حل مشكلة الانقطاع والترجمة) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        extracted_text = ""
        
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            max_pages = min(len(pdf.pages), 35) 
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += fix_extracted_text(text) + "\n"

        if not extracted_text.strip():
            return jsonify({'summary': 'الملف لا يحتوي على نص قابل للقراءة.'})

        # البرومبت المطور لمنع الانقطاع
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an expert academic summarizer. Your goal is to provide a COMPLETE, LONG, and UNINTERRUPTED summary. "
                        "Structure your response as follows: "
                        "1. A very long and detailed English summary inside <div class='en-text' dir='ltr'>. "
                        "2. A full, professional Arabic translation that matches the English version exactly. "
                        "DO NOT STOP halfway. Provide as much detail as possible for every section of the document."
                    )
                },
                {"role": "user", "content": f"Analyze and summarize this document completely:\n\n{extracted_text[:28000]}"}
            ],
            temperature=0.5,
            max_tokens=8000 # رفع الحد الأقصى جداً لمنع الانقطاع المذكور في صورتك
        )

        return jsonify({'summary': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

application = app

if __name__ == '__main__':
    app.run(debug=True)
