import os
import io
import PyPDF2
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

# تعريف التطبيق باسم 'app' ليتعرف عليه Vercel تلقائياً
app = Flask(__name__)
CORS(app)

# جلب مفتاح API من إعدادات Vercel
# تأكد من إضافة GROQ_API_KEY في الـ Environment Variables على Vercel
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
        if not data:
            return jsonify({'result': 'فشل في قراءة البيانات المرسلة'}), 400
            
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'result': 'يرجى إدخال موضوع للبحث'})

        system_content = (
            "You are a professional academic researcher. "
            "Reply in the language used by the user. "
            "Provide a very detailed academic report with clear headings, "
            "bullet points, and academic citations in Markdown format."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000 # زيادة السعة لتقارير أطول
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        print(f"Error in /generate: {str(e)}") # يظهر في سجلات Vercel Logs
        return jsonify({'result': f"حدث خطأ في النظام: {str(e)}"}), 500

# --- الميزة الثانية: تلخيص ملفات PDF ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'result': 'لم يتم العثور على ملف مرفوع'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'result': 'اسم الملف فارغ'}), 400

        # قراءة النص من الـ PDF في الذاكرة
        pdf_stream = io.BytesIO(file.read())
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        
        extracted_text = ""
        # استخراج أول 10 صفحات فقط لتجنب استهلاك الذاكرة العالي في Vercel
        max_pages = min(len(pdf_reader.pages), 10)
        for i in range(max_pages):
            page_text = pdf_reader.pages[i].extract_text()
            if page_text:
                extracted_text += page_text

        if not extracted_text.strip():
            return jsonify({'result': 'فشل استخراج النص. تأكد أن الملف يحتوي على نص وليس صوراً.'})

        # تنظيف النص وتحديده لعدم تجاوز حدود الـ Token
        clean_text = extracted_text[:10000]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت مساعد أكاديمي ذكي. لخص النص بأسلوب نقاط احترافية وشاملة باللغة العربية."},
                {"role": "user", "content": f"لخص المحتوى التالي تلخيصاً أكاديمياً:\n\n{clean_text}"}
            ],
            temperature=0.5
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        print(f"Error in /summarize_pdf: {str(e)}")
        return jsonify({'result': f"خطأ أثناء معالجة الملف: {str(e)}"}), 500

# ضروري لعمل Vercel بشكل صحيح
application = app

if __name__ == '__main__':
    app.run(debug=True)
