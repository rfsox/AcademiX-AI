import os
import io
import re
import base64
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# إعداد العميل - تأكد من وجود المفتاح في Environment Variables
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# الموديلات المستخدمة (Llama 3.3 هو الأقوى حالياً للتقارير)
MODEL_REPORT = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"
MODEL_VISION = "llama-3.2-11b-vision-preview"

def clean_text_for_ai(text):
    if not text: return ""
    # تنظيف النص مع الحفاظ على الحروف العربية والإنجليزية والترقيم المهم
    cleaned = re.sub(r'[^\w\s\.\!\?\u0600-\u06FF\-\:\(\)]', ' ', text)
    return " ".join(cleaned.split())

def extract_content(file_storage):
    extracted_text = ""
    try:
        file_storage.seek(0)
        file_bytes = file_storage.read()
        if not file_bytes: return ""
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # معالجة أول 15 صفحة لتجنب بطء Vercel
            for page in pdf.pages[:15]:
                content = page.extract_text()
                if content:
                    extracted_text += content + "\n"
    except Exception as e:
        print(f"Extraction Error: {e}")
    return clean_text_for_ai(extracted_text)

@app.route('/')
def index():
    return render_template('index.html')

# 1. محرك توليد التقارير الأكاديمية (ضخم وموثق)
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt: return jsonify({'report': 'يرجى إدخال الموضوع'})

        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": """أنت بروفيسور أكاديمي خبير. 
                مهمتك كتابة تقرير مفصل باللغة العربية يتضمن:
                1. مقدمة شاملة.
                2. محاور رئيسية مشروحة بعمق.
                3. جدول بيانات توضيحي (Markdown Table).
                4. استنتاجات علمية.
                5. قائمة مصادر ومراجع أكاديمية في النهاية.
                استخدم تنسيق Markdown (عناوين، نقاط، جداول)."""},
                {"role": "user", "content": f"اكتب بحثاً أكاديمياً حول: {prompt}"}
            ],
            temperature=0.6, # درجة حرارة متزنة للدقة الأكاديمية
            max_tokens=3500 
        )
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"خطأ في السيرفر: {str(e)}"}), 500

# 2. محرك التلخيص الذكي (ثنائي اللغة)
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files: return jsonify({'summary': 'الملف مفقود'}), 400
        raw_text = extract_content(request.files['file'])
        if not raw_text: return jsonify({'summary': 'لم يتم العثور على نص قابل للقراءة.'})

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "أنت خبير تلخيص. قدم ملخصاً تنفيذياً للنص: ابدأ بفقرة شاملة بالإنجليزية، ثم شرح مفصل بالنقاط باللغة العربية، ثم استخرج الكلمات المفتاحية."},
                {"role": "user", "content": f"Analyze this content:\n\n{raw_text[:12000]}"}
            ],
            temperature=0.3
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"خطأ تقني: {str(e)}"}), 500

# 3. محرك الأسئلة MCQ (مترجم واحترافي)
@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        if 'file' not in request.files: return jsonify({'error': 'ارفع ملف أولاً'}), 400
        raw_text = extract_content(request.files['file'])

        completion = client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": "قم بإنشاء 10 أسئلة اختيار من متعدد (MCQ). لكل سؤال: اكتبه بالإنجليزية ثم ترجمته العربية، ضع 4 خيارات، وحدد الإجابة الصحيحة في النهاية بنظام Markdown."},
                {"role": "user", "content": f"Create MCQs from this text:\n\n{raw_text[:12000]}"}
            ],
            temperature=0.5
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. محرك الرؤية (Vision) لحل المسائل بالصور
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        if 'image' not in request.files: return jsonify({'error': 'الصورة مفقودة'}), 400
        
        image_file = request.files['image']
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        completion = client.chat.completions.create(
            model=MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "قم بتحليل هذه الصورة. إذا كانت سؤالاً أكاديمياً، فقم بحله بالتفصيل مع الشرح باللغة العربية. إذا كانت رسماً بيانياً، فقم بتفسيره."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=2000
        )
        return jsonify({'solution': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f"خطأ في معالجة الصورة: {str(e)}"}), 500

# تشغيل التطبيق لبيئة Vercel
application = app

if __name__ == '__main__':
    # تشغيل محلي للتجربة
    app.run(host='0.0.0.0', port=5000, debug=False)
