@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    try:
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": """أنت خبير أكاديمي ثنائي اللغة. 
                المطلوب: تقديم شرح تلخيصي مفصل للنص.
                يجب أن يكون الشرح كالتالي:
                - العنوان الرئيسي بالعربي والإنجليزي.
                - الفقرات تشرح المفهوم بالعربي مع وضع المصطلحات العلمية بين قوسين بالإنجليزية.
                - إذا ذكرت نقاط مهمة، اكتب المصطلح بالإنجليزية ثم شرحه بالعربية."""},
                {"role": "user", "content": f"لخص هذا النص شرحاً وافياً مترجماً:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'summary': completion.choices[0].message.content})
    except Exception as e: return jsonify({'summary': str(e)}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    try:
        raw_text = extract_content(request.files['file'])
        completion = client.chat.completions.create(
            model=MODEL_REPORT,
            messages=[
                {"role": "system", "content": """أنت محترف في وضع الأسئلة الامتحانية. 
                صمم 10 أسئلة MCQ بناءً على النص المرفق.
                قواعد صارمة للتنسيق:
                1. السؤال: اكتب السؤال بالإنجليزية (EN) وتحته مباشرة ترجمته بالعربية (AR).
                2. الاختيارات: كل خيار (A, B, C, D) يجب أن يكتب بالإنجليزية ومعه ترجمته بالعربية في نفس السطر.
                3. الإجابة الصحيحة: وضح الخيار الصحيح مع كتابة التبرير العلمي بالعربي.
                مثال:
                EN: What is AI?
                AR: ما هو الذكاء الاصطناعي؟
                A) Artificial Intelligence / الذكاء الاصطناعي
                ... وهكذا.
                استخدم جداول Markdown أو تنسيق القوائم لتبدو مرتبة جداً."""},
                {"role": "user", "content": f"أنشئ الأسئلة من هذا النص:\n\n{raw_text[:12000]}"}
            ],
            max_tokens=6000
        )
        return jsonify({'questions': completion.choices[0].message.content})
    except Exception as e: return jsonify({'error': str(e)}), 500
