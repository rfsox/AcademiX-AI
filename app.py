import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# جلب المفتاح من Vercel Environment Variables
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        topic = data.get("topic")
        
        if not topic:
            return jsonify({'error': "يرجى إدخال عنوان التقرير"}), 400

        # البرومبت (Prompt) تم ضبطه ليكون مكثفاً جداً وأكاديمياً
        prompt = f"""اكتب تقريراً أكاديمياً مكثفاً وتفصيلياً عن: {topic}.
        يجب أن يتضمن التقرير:
        1. مقدمة عميقة.
        2. محاور رئيسية مشروحة بالتفصيل.
        3. تحليل للبيانات أو الأفكار المطروحة.
        4. استنتاجات وتوصيات.
        5. مراجع مقترحة.
        اجعل الأسلوب لغوياً رصيناً وباللغة العربية."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت خبير في كتابة التقارير الأكاديمية والمقالات البحثية المكثفة."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000 # رفع عدد التوكنز لضمان كثافة التقرير
        )
        
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
