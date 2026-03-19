import os
import io
import PyPDF2  # تأكد من إضافة PyPDF2 في ملف requirements.txt
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
            return jsonify({'result': 'يرجى إدخال موضوع للبحث'}) [cite: 60]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional academic researcher."}, [cite: 62]
                {"role": "user", "content": prompt} [cite: 63]
            ],
            temperature=0.7,
            max_tokens=4000, [cite: 63]
        )
        return jsonify({'result': completion.choices[0].message.content}) [cite: 63]
    except Exception as e:
        return jsonify({'result': f"خطأ: {str(e)}"})

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'result': 'لم يتم العثور على ملف'}) [cite: 64]
        
        file = request.files['file']
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read())) [cite: 65]
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() [cite: 65]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت مساعد أكاديمي. لخص النص التالي بأسلوب نقاط."}, [cite: 66]
                {"role": "user", "content": text[:12000]} [cite: 67]
            ]
        )
        return jsonify({'result': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'result': f"خطأ في الـ PDF: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
