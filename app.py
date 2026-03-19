import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# مكتبات اختيارية لمعالجة النص العربي المقلوب في ملفات PDF
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_TOOLS = True
except ImportError:
    HAS_ARABIC_TOOLS = False

app = Flask(__name__)
CORS(app)

# جلب مفتاح الأي بي آي
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

def fix_extracted_text(text):
    """دالة لمعالجة النص العربي لضمان فهمه بشكل صحيح من قبل النموذج"""
    if not text: return ""
    if HAS_ARABIC_TOOLS:
        # إعادة تشكيل الحروف وتصحيح الاتجاه
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير (محسن لنتائج أطول) ---
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
                        "أنت بروفيسور وأكاديمي خبير. قدم تقريراً بحثياً شاملاً ومفصلاً جداً باللغة العربية. "
                        "يجب أن يكون النص طويلاً ويتضمن مقدمة مكثفة، محاور تحليلية عميقة، استنتاجات، وقائمة مراجع. "
                        "استخدم Markdown لجعله يبدو كبحث مطبوع."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ في النظام: {str(e)}"}), 500

# --- 2. تلخيص PDF (تم تحديثه ليكون طويلاً وشاملاً جداً) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        extracted_text = ""
        
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            max_pages = min(len(pdf.pages), 30) # زيادة عدد الصفحات المقروءة
            for page in pdf.pages[:max_pages]:
                text = page.extract_text()
                if text:
                    # نطبق المعالجة لضمان جودة النص العربي المبعثر
                    extracted_text += fix_extracted_text(text) + "\n"

        if not extracted_text.strip():
            return jsonify({'summary': 'نعتذر، لم نتمكن من قراءة النص. تأكد أن الملف ليس صوراً فقط.'})

        # طلب تلخيص طويل جداً ومزدوج
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a master academic analyst. Your task is to provide an EXTREMELY DETAILED and LONG summary. "
                        "1. Breakdown the document into its original sections. "
                        "2. For each section, provide a comprehensive English analysis inside <div class='en-text' dir='ltr'>. "
                        "3. Directly follow it with a high-quality, professional Arabic translation. "
                        "Don't skip any details. The output must be long enough to cover all aspects of the document."
                    )
                },
                {"role": "user", "content": f"Please summarize this document thoroughly:\n\n{extracted_text[:25000]}"}
            ],
            temperature=0.5,
            max_tokens=4000
        )

        return jsonify({'summary': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# لضمان التشغيل على Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True)
