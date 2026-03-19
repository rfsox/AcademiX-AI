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

# الموديلات المستخدمة
MODEL_LARGE = "llama-3.3-70b-versatile" # للتقارير الضخمة
MODEL_FAST = "llama-3.1-8b-instant"     # للتلخيص والأسئلة (لتجنب الـ Rate Limit)

def extract_clean_text(file_storage):
    """استخراج النص من PDF بكفاءة"""
    extracted_text = ""
    try:
        # قمنا بتصفير المؤشر لضمان قراءة الملف من البداية
        file_storage.seek(0)
        with pdfplumber.open(io.BytesIO(file_storage.read())) as pdf:
            # قراءة أول 40 صفحة
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
            model=MODEL_LARGE,
            messages=[
                {
                    "role": "system", 
                    "content": "أنت بروفيسور خبير. اكتب تقريراً أكاديمياً ضخماً ومفصلاً جداً (أكثر من 2000 كلمة). استخدم لغة عربية سليمة ونسق العناوين بوضوح."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8000 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ: {str(e)}"}), 500

# --- 2. تلخيص PDF (تم التحديث لتجنب 429) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        text = extract_clean_text(request.files['file'])
        if not text.strip():
            return jsonify({'summary': 'الملف لا يحتوي على نص قابل للقراءة.'})

        completion = client.chat.completions.create(
            model=MODEL_FAST, # استخدمنا الموديل الأسرع هنا لضمان النجاح
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an academic expert. Provide a MASSIVE and DETAILED summary. "
                        "Instructions: Write a detailed English paragraph, followed by its Professional Arabic translation. "
                        "Ensure Arabic text is natural and correctly formatted. "
                        "Don't provide a short summary; go into details."
                    )
                },
                {"role": "user", "content": f"Analyze and summarize this text in depth:\n\n{text[:20000]}"}
            ],
            temperature=0.5,
            max_tokens=5000 # 5000 توكن كافية جداً للتلخيص وبدون مشاكل ليميت
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        if "rate_limit_exceeded" in str(e).lower():
            return jsonify({'summary': "⚠️ وصلت للحد المسموح به مجاناً حالياً. حاول مجدداً بعد قليل."}), 429
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# --- 3. مصنع الأسئلة MCQ (ترجمة مقابلة + لغة سليمة) ---
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'يرجى إرفاق ملف'}), 400
        
        text = extract_clean_text(request.files['file'])
        if not text.strip():
            return jsonify({'error': 'الملف فارغ'})

        completion = client.chat.completions.create(
            model=MODEL_FAST, # الموديل السريع يضمن توليد عدد أسئلة ضخم بدون انقطاع
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "أنت خبير وضع امتحانات. قم بتوليد بنك أسئلة MCQ ضخم. "
                        "قاعدة التنسيق: \n"
                        "1. السؤال بالإنجليزية.\n"
                        "2. السؤال بالعربية مباشرة.\n"
                        "3. الخيارات A, B, C, D مترجمة للغتين.\n"
                        "4. الإجابة الصحيحة تحت الخيارات مع شرح عربي.\n"
                        "تأكد أن اللغة العربية سليمة 100% وغير معكوسة."
                    )
                },
                {"role": "user", "content": f"Generate as many MCQs as possible from this text:\n\n{text[:20000]}"}
            ],
            temperature=0.6,
            max_tokens=6000 
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f"خطأ في توليد الأسئلة: {str(e)}"}), 500

application = app
if __name__ == '__main__':
    app.run(debug=True)
