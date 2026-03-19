import os
import io
import pdfplumber
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# تأكد من وضع المفتاح في إعدادات Vercel باسم GROQ_API_KEY
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

# نستخدم الموديلات الأسرع لتجنب الـ Timeout في Vercel
MODEL_QUICK = "llama-3.1-8b-instant"   # سريع جداً للأسئلة
MODEL_POWER = "llama-3.3-70b-versatile" # قوي جداً للتلخيص والتقارير

def get_pdf_text(file):
    """استخراج النص بذكاء من أول 10 صفحات لضمان السرعة"""
    text = ""
    try:
        file.seek(0)
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            pages = pdf.pages[:10] # نكتفي بـ 10 صفحات لضمان استقرار السيرفر المجاني
            for page in pages:
                content = page.extract_text()
                if content: text += content + "\n"
    except: pass
    return text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        chat_completion = client.chat.completions.create(
            model=MODEL_POWER,
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي محترف. اكتب تقارير طويلة ومنظمة بأسلوب Markdown."},
                {"role": "user", "content": f"اكتب تقريراً مفصلاً عن: {prompt}"}
            ],
            max_tokens=4000
        )
        return jsonify({'report': chat_completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'report': f"Error: {str(e)}"}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        text = get_pdf_text(request.files['file'])
        if not text: return jsonify({'summary': "تعذر قراءة الملف"}), 400

        response = client.chat.completions.create(
            model=MODEL_POWER,
            messages=[
                {"role": "system", "content": "أنت خبير تلخيص أكاديمي. اشرح المادة العلمية بأسلوب فقرات مترجمة (عربي/إنجليزي) وضع المصطلحات المهمة بين قوسين."},
                {"role": "user", "content": f"لخص هذا النص شرحاً وافياً:\n\n{text[:10000]}"}
            ],
            max_tokens=3000
        )
        return jsonify({'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'summary': f"خطأ في السيرفر: {str(e)}"}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        text = get_pdf_text(request.files['file'])
        if not text: return jsonify({'error': "الملف فارغ"}), 400

        # هنا السر في السرعة: نستخدم الموديل الاصغر 8b لكي لا يحدث Timeout
        response = client.chat.completions.create(
            model=MODEL_QUICK,
            messages=[
                {"role": "system", "content": """أنت محترف أسئلة MCQ. صمم 15 سؤالاً من النص المرفق.
                يجب أن يكون التنسيق ثنائي اللغة تماماً كالتالي:
                EN: Question text?
                AR: ترجمة السؤال؟
                A) Option EN / الترجمة العربية
                B) Option EN / الترجمة العربية
                C) Option EN / الترجمة العربية
                D) Option EN / الترجمة العربية
                Answer: [الخيار الصحيح]"""},
                {"role": "user", "content": f"أنشئ 15 سؤالاً مترجماً بدقة من المنهج التالي:\n\n{text[:8000]}"}
            ],
            temperature=0.3, # لزيادة الدقة في المنهج
            max_tokens=3000
        )
        return jsonify({'questions': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f"Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
