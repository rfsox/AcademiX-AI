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
        # أضفنا خيار اللغة (اختياري، إذا لم يرسله الفرونت إند سيكتشفه الذكاء الاصطناعي)
        language = data.get("language", "auto") 
        
        if not topic:
            return jsonify({'error': "يرجى إدخال عنوان التقرير"}), 400

        # برومبت ذكي يحدد اللغة بناءً على المدخلات
        system_instruction = "You are an expert academic writer. You write dense, high-quality, and detailed professional reports."
        
        prompt = f"""Write a comprehensive and intensive academic report about: {topic}.
        The report must include:
        1. Executive Summary/Introduction.
        2. Detailed main sections and analysis.
        3. Data-driven insights or theoretical framework.
        4. Conclusion and Recommendations.
        5. Suggested Academic References.
        
        Important Instructions:
        - If the language requested is 'Arabic' or the topic is in Arabic, write the entire report in formal Arabic.
        - If the language requested is 'English' or the topic is in English, write the entire report in academic English.
        - Ensure the style is professional, dense (lengthy), and suitable for university-level submissions.
        - Language to use: {language} (if 'auto', detect from the topic).
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6, # تقليل الحرارة قليلاً لزيادة الدقة الأكاديمية
            max_tokens=8000 
        )
        
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
