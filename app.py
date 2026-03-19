import os
import io
import PyPDF2  # مكتبة معالجة ملفات PDF الجديدة
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# تأكد من وضع مفتاحك في إعدادات Vercel (Environment Variables) 
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/')
def index():
    # فتح الصفحة الرئيسية من مجلد templates 
    return render_template('index.html')

# --- الميزة الأولى: توليد التقارير الأكاديمية (الكود القديم كما هو) --- [cite: 39]
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'result': 'يرجى إدخال موضوع للبحث'}) [cite: 39]

        system_content = (
            "You are a professional academic researcher. "
            "If the user asks in Arabic, you MUST reply with a very detailed, long, and well-formatted academic report in Arabic. " [cite: 40]
            "If the user asks in English, you MUST reply with a very detailed, long, and well-formatted academic report in English. " [cite: 41]
            "Use Markdown for formatting, including bold titles, bullet points, and clear sections."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # الموديل المحدث [cite: 42]
            messages=[
                {"role": "system", "content": system_content}, [cite: 42]
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000, [cite: 43]
        )

        return jsonify({'result': completion.choices[0].message.content}) [cite: 43]

    except Exception as e:
        return jsonify({'result': f"حدث خطأ في النظام: {str(e)}"}) [cite: 43]

# --- الميزة الثانية الجديدة: تلخيص ملفات PDF (إضافة جديدة) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        # التحقق من وجود ملف مرسل
        if 'file' not in request.files:
            return jsonify({'result': 'لم يتم العثور على ملف مرفوع'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'result': 'اسم الملف فارغ'})

        # قراءة النص من داخل الـ PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text()

        if not extracted_text.strip():
            return jsonify({'result': 'فشل استخراج النص من الملف. تأكد أن ملف الـ PDF يحتوي على نصوص وليس صوراً فقط.'})

        # إرسال النص للذكاء الاصطناعي للتلخيص
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت مساعد أكاديمي ذكي. قم بتلخيص النص الأكاديمي التالي بأسلوب نقاط مركزة واحترافية باللغة العربية."},
                {"role": "user", "content": f"لخص هذا النص الأكاديمي المستخرج من المحاضرة:\n\n{extracted_text[:12000]}"} # نأخذ أول 12 ألف حرف لضمان عدم تخطي الحدود
            ],
            temperature=0.5,
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'result': f"خطأ أثناء معالجة ملف PDF: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
