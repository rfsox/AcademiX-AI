import os
import io
import PyPDF2 # تم فصل التعليق لضمان سلامة الاستيراد في Vercel
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# تعريف التطبيق باسم 'app' ليتعرف عليه Vercel تلقائياً
app = Flask(__name__)
CORS(app)

# جلب مفتاح API من إعدادات Vercel
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/')
def index():
    # استدعاء صفحة الواجهة من مجلد templates
    return render_template('index.html')

# --- الميزة الأولى: توليد التقارير الأكاديمية ---
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'result': 'يرجى إدخال موضوع للبحث'})

        system_content = (
            "You are a professional academic researcher. "
            "If the user asks in Arabic, you MUST reply with a very detailed, long, and well-formatted academic report in Arabic. "
            "If the user asks in English, you MUST reply with a very detailed, long, and well-formatted academic report in English. "
            "Use Markdown for formatting, including bold titles and clear sections."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # الموديل الأحدث والمستقر
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'result': f"حدث خطأ في النظام: {str(e)}"})

# --- الميزة الثانية: تلخيص ملفات PDF ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'result': 'لم يتم العثور على ملف مرفوع'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'result': 'اسم الملف فارغ'})

        # قراءة النص من الـ PDF في الذاكرة لسرعة الأداء على Vercel
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text()

        if not extracted_text.strip():
            return jsonify({'result': 'تأكد أن ملف الـ PDF يحتوي على نصوص وليس صوراً فقط.'})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت مساعد أكاديمي ذكي. قم بتلخيص النص الأكاديمي التالي بأسلوب نقاط مركزة واحترافية باللغة العربية."},
                {"role": "user", "content": f"لخص هذا النص:\n\n{extracted_text[:12000]}"}
            ],
            temperature=0.5
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'result': f"خطأ أثناء معالجة الملف: {str(e)}"})

# نقطة الانطلاق الأساسية لـ Vercel
if __name__ == '__main__':
    app.run(debug=True)
