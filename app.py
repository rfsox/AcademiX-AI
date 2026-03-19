import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# تأكد من إضافة GROQ_API_KEY في إعدادات Vercel
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_research', methods=['POST'])
def generate_research():
    try:
        topic = request.json.get("topic")
        if not topic:
            return jsonify({'research': "يرجى إدخال موضوع"}), 400

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت خبير أكاديمي. اكتب بحثاً مفصلاً باللغة العربية مع مقدمة، محاور، وخاتمة."},
                {"role": "user", "content": f"اكتب بحثاً عن: {topic}"}
            ],
        )
        # إرسال النص كما هو، الـ Frontend سيتولى التنسيق
        return jsonify({'research': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'research': f"خطأ في السيرفر: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
