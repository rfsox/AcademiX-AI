@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_content(request.files['file'])
        
        # قمنا بتقليل العدد لـ 15 سؤالاً لضمان عدم حدوث Timeout في Vercel
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": """أنت خبير أكاديمي. استخرج 15 سؤال MCQ دقيق من النص.
                يجب أن يكون التنسيق ثنائي اللغة:
                EN: Question
                AR: الترجمة
                A) Option / الترجمة
                Answer: [الخيار]"""},
                {"role": "user", "content": f"أنشئ 15 سؤالاً من هذا النص:\n\n{raw_text[:10000]}"}
            ],
            temperature=0.4,
            max_tokens=3000 # تقليل التوكنز لسرعة الاستجابة
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e: 
        # طباعة الخطأ في سجلات Vercel لمعرفته بدقة
        print(f"Error: {str(e)}")
        return jsonify({'error': "السيرفر استغرق وقتاً طويلاً، حاول مرة أخرى بملف أصغر"}), 500
