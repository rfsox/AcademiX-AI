import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# جلب المفتاح من إعدادات Vercel
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        topic = data.get("topic")
        language = data.get("language", "auto") 
        
        if not topic:
            return jsonify({'error': "Please enter a topic"}), 400

        # نظام تعليمات "عسكري" لضمان الكثافة وعدم وجود كلام زائد
        system_instruction = """You are a high-level Senior Academic Researcher.
        STRICT RULES:
        1. DO NOT say "Here is the report" or "Sure" or any introductory text.
        2. START IMMEDIATELY with the report title.
        3. CONTENT DENSITY: Provide a VERY DENSE and technical report (minimum 1500 words if possible).
        4. FORMATTING: Use professional Markdown. Headers must be clear (##, ###).
        5. ENGLISH REPORTS: Must be strictly Left-to-Right and use advanced scientific terminology.
        6. NO CHATTER: Only output the final report ready for copying."""
        
        prompt = f"""Write an EXTREMELY INTENSIVE and detailed academic report about: {topic}.
        
        REQUIRED SECTIONS (Make them very long and technical):
        - Title of the Report.
        - Abstract & Executive Summary.
        - Detailed Introduction.
        - Literature Review & Theoretical Framework.
        - Core Technical Analysis (Deep Dive).
        - Global Impact & Case Studies.
        - Future Projections & Recommendations.
        - Comprehensive Conclusion.
        - Academic Bibliography/References.

        Language to use: {language} (Detect from input).
        Target: Ready-to-copy, high-density academic content only."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4, # تقليلها أكثر لزيادة التركيز والرزانة العلمية
            max_tokens=8000  # رفع السقف لأقصى حد لضمان كثافة التقرير
        )
        
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
