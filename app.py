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
        
        if not topic:
            return jsonify({'error': "Please enter a topic"}), 400

        # تعليمات صارمة (نظام كتابة أكاديمي مكثف)
        system_instruction = """You are an Elite Academic Report Generator.
        STRICT OPERATING PROCEDURES:
        1. NO PREAMBLE: Do not say 'Here is the report' or 'Certainly'. Start with the Title immediately.
        2. DENSITY MAXIMIZATION: Each section must be extremely long, technical, and detailed. 
        3. FORMATTING: Use Markdown (## for Main Headers). 
        4. ALIGNMENT: If the topic is in English, use complex academic English.
        5. NO CHATTER: Only provide the report content.
        6. SCIENTIFIC RIGOR: Include technical data, theoretical frameworks, and deep analysis."""
        
        prompt = f"""Generate a MASTER-LEVEL academic report about: {topic}.
        
        Structure the report as follows (Expand each section to the maximum):
        ## [Title of the Report]
        - **Executive Summary**: High-level overview.
        - **Introduction**: Background, Problem Statement, and Objectives.
        - **Literature Review**: Historical and current research landscape.
        - **Detailed Technical Analysis**: The core deep-dive (Very long section).
        - **Methodological Framework / Theoretical Basis**.
        - **Global Implications & Economic Impact**.
        - **Challenges and Future Projections**.
        - **Conclusion & Strategic Recommendations**.
        - **References**: List academic sources.

        Ensure the language matches the topic's language. 
        Start immediately with the title."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # تقليل الحرارة لضمان عدم التكرار وزيادة الدقة
            max_tokens=8000  # السماح بأكبر قدر من النص
        )
        
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
