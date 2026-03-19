import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import markdown

app = Flask(__name__)

# --- الأمان أولاً ---
# بدال ما تحط المفتاح هنا، استخدم الـ Environment Variable في Vercel
API_KEY = os.getenv("GEMINI_API_KEY") 
if not API_KEY:
    # هذا بس للتشغيل المحلي، بس بالرفع لازم تمسحه
    API_KEY = "AIzaSy..." 

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # استخدم فلاش أسرع وأرخص

# دالة مساعدة لمعالجة النصوص بدل التكرار
def get_ai_response(prompt):
    try:
        response = model.generate_content(prompt)
        return markdown.markdown(response.text)
    except Exception as e:
        return f"خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    prompt = f"أجب كمساعد أكاديمي ذكي: {user_input}"
    return jsonify({"response": get_ai_response(prompt)})

@app.route('/generate_research', methods=['POST'])
def generate_research():
    topic = request.json.get("topic")
    prompt = f"اكتب بحثاً أكاديمياً مفصلاً عن: {topic}. استخدم مراجع ومصادر واجعل الأسلوب علمي رصين."
    return jsonify({"research": get_ai_response(prompt)})

# ... (باقي الـ Routes بنفس الطريقة المختصرة)

if __name__ == '__main__':
    app.run(debug=True)
