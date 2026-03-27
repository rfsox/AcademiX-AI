import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

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

        # نظام تعليمات صارم لضمان التنسيق والكثافة
        system_instruction = """You are a professional academic researcher. 
        Your task is to provide DENSE, TECHNICAL, and WELL-FORMATTED reports.
        - Use Markdown (## for headers, **bold** for key terms, and bullet points).
        - Ensure structural consistency.
        - If English, use high-level academic vocabulary."""
        
        prompt = f"""Generate an intensive academic report about: {topic}.
        
        Structure Requirements:
        1. Abstract/Executive Summary.
        2. Introduction & Background.
        3. Core Analysis & Technical Discussion (Very Dense).
        4. Findings & Implications.
        5. Conclusion & Recommendations.
        6. Academic References.

        Language Instructions:
        - Language: {language} (Detect from topic if 'auto').
        - If English: Use Professional Academic English, left-to-right.
        - If Arabic: Use Formal Arabic (Fusha), right-to-left.
        - Length: Maximum detail possible.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5, # درجة حرارة منخفضة لضمان عدم الهلوسة والدقة الأكاديمية
            max_tokens=4000
        )
        
        return jsonify({'report': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
