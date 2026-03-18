import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# تأكد من وضع مفتاحك في إعدادات Vercel (Environment Variables)
# استبدل "YOUR_GROQ_API_KEY" بمفتاحك الفعلي في بيئة العمل السحابية
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/')
def index():
    # فتح الصفحة الرئيسية من مجلد templates
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # استلام البيانات من الجافاسكريبت
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'result': 'يرجى إدخال موضوع للبحث'})

        # إعدادات النظام لضمان تقرير أكاديمي طويل ومنسق باللغتين
        system_content = (
            "You are a professional academic researcher. "
            "If the user asks in Arabic, you MUST reply with a very detailed, long, and well-formatted academic report in Arabic. "
            "If the user asks in English, you MUST reply with a very detailed, long, and well-formatted academic report in English. "
            "Use Markdown for formatting, including bold titles, bullet points, and clear sections."
        )

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000, # زيادة عدد الكلمات لضمان تقرير طويل
            top_p=1,
            stream=False,
            stop=None,
        )

        result = completion.choices[0].message.content
        return jsonify({'result': result})

    except Exception as e:
        # معالجة الأخطاء وإرسالها لواجهة المستخدم بشكل نصي واضح
        return jsonify({'result': f"حدث خطأ في النظام: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
