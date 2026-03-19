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
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

# --- الميزة الأولى: توليد التقارير الأكاديمية ---
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'result': 'فشل في قراءة البيانات'}), 400
            
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'result': 'يرجى إدخال موضوع للبحث'})

        system_content = (
            "You are a professional academic researcher. "
            "Reply in the language used by the user. "
            "Provide a detailed academic report with headings and citations."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'result': f"حدث خطأ: {str(e)}"}), 500

# --- الميزة الثانية: تلخيص PDF (إنجليزي + عربي خبط) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'result': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        pdf_stream = io.BytesIO(file.read())
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        
        extracted_text = ""
        # نأخذ أول 8 صفحات لضمان استجابة سريعة ودقيقة
        max_pages = min(len(pdf_reader.pages), 8)
        for i in range(max_pages):
            page_text = pdf_reader.pages[i].extract_text()
            if page_text:
                extracted_text += page_text

        if not extracted_text.strip():
            return jsonify({'result': 'الملف لا يحتوي على نص قابل للقراءة.'})

        # إرسال التعليمات لعمل تلخيص مزدوج (خبط لغوي)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a bilingual academic expert. "
                        "Summarize the text in a 'Bilingual Mixed' format. "
                        "For every point you make, write the bullet point in English first, "
                        "then immediately write its professional Arabic translation below it. "
                        "Example format:\n"
                        "- **English sentence here**\n"
                        "  (الترجمة العربية الاحترافية هنا)\n"
                        "Use Markdown for bolding and clear structure."
                    )
                },
                {"role": "user", "content": f"Summarize this text:\n\n{extracted_text[:10000]}"}
            ],
            temperature=0.6
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'result': f"خطأ أثناء المعالجة: {str(e)}"}), 500

application = app

if __name__ == '__main__':
    app.run(debug=True)
