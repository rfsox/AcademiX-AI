import os
import io
import pdfplumber 
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# مكتبات اختيارية لإصلاح ترتيب النصوص العربية إذا استخرجت مقلوبة
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_FIX = True
except ImportError:
    HAS_ARABIC_FIX = False

app = Flask(__name__)
CORS(app)

# إعداد عميل Groq
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

def process_arabic_pdf_text(text):
    """دالة لتحسين قراءة النص العربي المستخرج من PDF"""
    if not text:
        return ""
    if HAS_ARABIC_FIX:
        # هذه الخطوة تحول النص من "س ك ع" إلى "عكس" ليقرأه الذكاء الاصطناعي صح
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير (تحسين جودة الرد الأكاديمي) ---
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
                        "أنت بروفيسور أكاديمي خبير. قدم تقريراً شاملاً باللغة العربية بتنسيق Markdown. "
                        "يجب أن يكون التقرير طويلاً، منظماً بعناوين، ويتضمن مراجع علمية في النهاية."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"حدث خطأ في النظام: {str(e)}"}), 500

# --- 2. تلخيص PDF (حل مشكلة النصوص المقلوبة) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        extracted_text = ""
        
        # استخدام pdfplumber لقراءة احترافية
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            max_pages = min(len(pdf.pages), 20) 
            for page in pdf.pages[:max_pages]:
                text = page.extract_text()
                if text:
                    # تطبيق معالجة النص لضمان فهم الذكاء الاصطناعي للمحتوى العربي
                    extracted_text += process_arabic_pdf_text(text) + "\n"

        if not extracted_text.strip() or len(extracted_text) < 10:
            return jsonify({'summary': 'فشل في استخراج نص واضح. قد يكون الملف محمياً أو عبارة عن صور فقط.'})

        # إرسال النص المعالج إلى Groq للتلخيص المزدوج
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "أنت مترجم ومحلل أكاديمي. قم بتلخيص النص التالي بأسلوب احترافي. "
                        "أولاً: قدم ملخصاً تفصيلياً باللغة الإنجليزية داخل وسم <div class='en-text' dir='ltr'>. "
                        "ثانياً: قدم نفس التلخيص باللغة العربية وبدقة عالية. "
                        "حافظ على المصطلحات العلمية."
                    )
                },
                {"role": "user", "content": f"Summarize this content:\n\n{extracted_text[:18000]}"}
            ],
            temperature=0.5,
            max_tokens=4000
        )

        return jsonify({'summary': completion.choices[0].message.content})

    except Exception as e:
        print(f"Error detail: {e}")
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# لضمان العمل على Vercel أو السيرفر المحلي
application = app

if __name__ == '__main__':
    app.run(debug=True)
