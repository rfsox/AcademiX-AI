// static/script.js

async function generateReport() {
    const promptInput = document.getElementById('promptInput');
    const resultDiv = document.getElementById('result');
    const reportWrapper = document.getElementById('reportWrapper');
    const loader = document.getElementById('loader');

    const prompt = promptInput.value;

    if (!prompt) {
        alert("يرجى إدخال موضوع البحث أولاً!");
        return;
    }

    // إظهار اللودر وإخفاء النتائج السابقة
    loader.style.display = 'block';
    reportWrapper.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: prompt }),
        });

        const data = await response.json();

        if (data.result) {
            // --- التعديل الجوهري للغة واتجاه النص ---
            // 'auto' تجعل المتصفح يكتشف اللغة: إذا بدأت بعربي يقلب اليمين، وإذا إنجليزي يقلب يسار
            resultDiv.style.direction = "auto"; 
            resultDiv.style.textAlign = "start"; 
            
            // تحويل نص الـ Markdown القادم من السيرفر إلى HTML (إذا كنت تستخدم مكتبة marked)
            // أو عرضه كنص عادي إذا لم تكن تستخدمها:
            resultDiv.innerText = data.result; 

            // إظهار حاوية التقرير
            reportWrapper.style.display = 'block';
        } else {
            resultDiv.innerText = "فشل توليد التقرير، حاول مرة أخرى.";
        }
    } catch (error) {
        console.error("Error:", error);
        resultDiv.innerText = "حدث خطأ في الاتصال بالسيرفر.";
    } finally {
        loader.style.display = 'none';
    }
}
