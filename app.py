import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# إعداد Groq - تأكد من وضع مفتاحك هنا
# استبدل "YOUR_GROQ_API_KEY" بمفتاحك الفعلي
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
            return jsonify({'result': 'يرجى إدخال موضوع للبحث!'})

        # إعدادات النظام لضمان تقرير أكاديمي طويل ومنسق [cite: 2, 3]
        system_content = (
            "أنت مساعد أكاديمي محترف وموثق. مهمتك هي كتابة تقارير جامعية شاملة باللغة العربية. "
            "يجب أن يتضمن ردك دائماً: "
            "1. مقدمة أكاديمية رصينة. "
            "2. عناوين فرعية واضحة (عن طريق Markdown). "
            "3. شرح مفصل جداً وموسع لكل نقطة. "
            "4. قائمة مراجع (Citations) حقيقية في نهاية التقرير. "
            "5. اجعل النص طويلاً جداً لضمان تغطية كافة جوانب الموضوع."
        )

        # طلب التوليد من موديل Llama 
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"اكتب تقرير أكاديمي مفصل جداً وموسع عن: {prompt}"}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7, 
            max_tokens=8000, # لضمان أقصى طول للنص 
            top_p=1,
            stream=False,
        )

        # استخراج النص الناتج
        report_result = chat_completion.choices[0].message.content

        # إرسال النتيجة بنجاح
        return jsonify({'result': report_result})

    except Exception as e:
        # معالجة الخطأ بشكل صحيح لتجنب رسالة "cite is not defined"
        error_message = f"عذراً مهندس رضا، حدث خطأ فني: {str(e)}"
        print(error_message) # يظهر في Terminal الـ VS Code
        return jsonify({'result': error_message})

# تشغيل السيرفر على المنفذ 5000
if __name__ == '__main__':
    app.run(debug=True, port=5000)