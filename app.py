import os
import io
import PyPDF2
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'result': 'يرجى إدخال موضوع'})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert researcher. Provide a VERY LONG, extremely detailed academic report with many sections and citations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000 # أقصى حد مسموح به لضمان طول التقرير
        )
        return jsonify({'result': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'result': f"خطأ: {str(e)}"}), 500

# --- ميزة التلخيص العميق جداً (إنجليزي + عربي) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'result': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        pdf_stream = io.BytesIO(file.read())
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        
        extracted_text = ""
        # رفعنا عدد الصفحات إلى 20 صفحة للحصول على محتوى ضخم
        max_pages = min(len(pdf_reader.pages), 20) 
        for i in range(max_pages):
            page_text = pdf_reader.pages[i].extract_text()
            if page_text:
                extracted_text += f"\n--- Page {i+1} ---\n" + page_text

        if not extracted_text.strip():
            return jsonify({'result': 'الملف فارغ أو عبارة عن صور.'})

        # إرسال نص طويل جداً (حتى 25 ألف حرف)
        clean_text = extracted_text[:25000] 

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a bilingual academic professor. Your task is to provide an EXHAUSTIVE and VERY DETAILED summary. "
                        "Do not skip any important details. For every section of the text: "
                        "1. Write a comprehensive summary in English. "
                        "2. Follow it with an EQUALLY DETAILED professional Arabic translation. "
                        "Format: \n"
                        "### [Section Title in English]\n"
                        "**Detailed English Summary...**\n\n"
                        "**التلخيص العربي المفصل...**\n"
                        "-----------------------------------\n"
                        "Make the response as long as possible."
                    )
                },
                {"role": "user", "content": f"Analyze and summarize this text in great detail:\n\n{clean_text}"}
            ],
            temperature=0.5,
            max_tokens=4000 # طلب أقصى عدد من الكلمات في الرد
        )

        return jsonify({'result': completion.choices[0].message.content})

    except Exception as e:
        return jsonify({'result': f"خطأ في المعالجة العميق: {str(e)}"}), 500

application = app

if __name__ == '__main__':
    app.run(debug=True)
