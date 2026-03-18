// static/script.js

async function generateReport() {
    const promptInput = document.getElementById('promptInput');
    const outputContent = document.getElementById('outputContent');
    const reportWrapper = document.getElementById('reportWrapper');
    const loader = document.getElementById('loader');
    const pdfBtn = document.getElementById('pdfBtn');
    const citations = document.getElementById('citations');

    const prompt = promptInput.value;

    if (!prompt) {
        alert("يرجى إدخال موضوع البحث أولاً!");
        return;
    }

    // إظهار اللودر وإخفاء النتائج السابقة وزر PDF
    loader.style.display = 'block';
    reportWrapper.style.display = 'none';
    pdfBtn.style.display = 'none';

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
            // ضبط اتجاه النص تلقائياً (يمين للعربي / يسار للإنجليزي)
            outputContent.style.direction = "auto";
            outputContent.style.textAlign = "start";

            // استخدام مكتبة marked لتحويل Markdown إلى HTML جميل
            outputContent.innerHTML = marked.parse(data.result);

            // تحديث المراجع (إذا كان الذكاء الاصطناعي يفصلها في الرد)
            // هنا سنعرض النتيجة كاملة داخل المنطقة المخصصة
            reportWrapper.style.display = 'block';
            pdfBtn.style.display = 'flex'; // إظهار زر PDF بعد النجاح
            
            // إضافة نقاط وهمية للمستخدم لزيادة الحماس (اختياري)
            const points = document.getElementById('userPoints');
            points.innerText = parseInt(points.innerText) + 10;
        } else {
            outputContent.innerText = "فشل توليد التقرير، حاول مرة أخرى.";
        }
    } catch (error) {
        console.error("Error:", error);
        outputContent.innerText = "حدث خطأ في الاتصال بالسيرفر.";
    } finally {
        loader.style.display = 'none';
    }
}

// وظيفة تصدير التقرير إلى ملف PDF
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    const options = {
        margin:       1,
        filename:     'Academic_Report.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    // تنفيذ عملية التحويل والتحميل
    html2pdf().set(options).from(element).save();
}
