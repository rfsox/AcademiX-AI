import os
import io
import pdfplumber  # استبدلنا PyPDF2 بمكتبة أقوى وأدق
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# جلب مفتاح الأي بي آي
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. مولد التقارير المحدث ---
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
                        "أنت خبير أبحاث أكاديمي عالمي. قدم تقريراً طويلاً جداً ومفصلاً باللغة العربية. "
                        "يجب أن يتضمن التقرير: مقدمة، محاور رئيسية، شرحاً علمياً، استنتاجات، وقائمة مراجع أكاديمية. "
                        "استخدم تنسيق Markdown بشكل احترافي مع عناوين واضحة."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000 
        )
        # أصلحنا المفتاح ليكون 'report' بدلاً من 'result'
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"حدث خطأ في النظام: {str(e)}"}), 500

# --- 2. ميزة التلخيص المزدوج (حل مشكلة الصورة رقم 7) ---
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'summary': 'لم يتم العثور على ملف'}), 400
        
        file = request.files['file']
        extracted_text = ""
        
        # استخدام pdfplumber لقراءة أدق للنصوص والجداول
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            max_pages = min(len(pdf.pages), 25) # قراءة حتى 25 صفحة
            for page in pdf.pages[:max_pages]:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        if not extracted_text.strip():
            return jsonify({'summary': 'نعتذر، لم أتمكن من استخراج نص من هذا الملف (قد يكون الملف عبارة عن صور فقط).'})

        # معالجة النص عبر Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a professional academic translator and summarizer. "
                        "Analyze the text and provide a dual summary for each major section: "
                        "First in English (Very Detailed), then the exact Arabic translation. "
                        "Format the output using HTML tags for clarity: "
                        "Use <div class='en-text'> for English and standard text for Arabic. "
                        "Make the final response as comprehensive as possible."
                    )
                },
                {"role": "user", "content": f"Summarize this academic document:\n\n{extracted_text[:20000]}"}
            ],
            temperature=0.5,
            max_tokens=4000
        )

        return jsonify({'summary': completion.choices[0].message.content})

    except Exception as e:
        print(f"Internal Error: {e}")
        return jsonify({'summary': f"خطأ تقني في معالجة الملف: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
