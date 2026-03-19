// static/script.js

// --- الميزة الأولى: توليد التقارير النصية (الكود القديم مع تحسينات) ---
async function generateReport() {
    const promptInput = document.getElementById('promptInput');
    const outputContent = document.getElementById('outputContent');
    const reportWrapper = document.getElementById('reportWrapper');
    const loader = document.getElementById('loader');
    const pdfBtn = document.getElementById('pdfBtn');

    const prompt = promptInput.value;

    if (!prompt) {
        alert("يرجى إدخال موضوع البحث أولاً!");
        return;
    }

    // إظهار اللودر وإخفاء النتائج السابقة
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
            outputContent.style.direction = "rtl";
            outputContent.style.textAlign = "right";

            // تحويل Markdown إلى HTML
            outputContent.innerHTML = marked.parse(data.result);
            
            reportWrapper.style.display = 'block';
            pdfBtn.style.display = 'flex'; // إظهار زر PDF
            
            // تحديث نقاط المستخدم
            updateUserPoints(10);
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

// --- الميزة الثانية: معالجة ورفع ملف الـ PDF (إضافة جديدة) ---
// ننتظر تحميل الصفحة لربط مستمع الأحداث لملف الرفع
document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = document.getElementById('pdfUpload');
    if (pdfUpload) {
        pdfUpload.addEventListener('change', async function() {
            const file = this.files[0];
            if (!file) return;

            // تجهيز البيانات كـ FormData لإرسال الملف
            const formData = new FormData();
            formData.append('file', file);

            const loader = document.getElementById('loader');
            const reportWrapper = document.getElementById('reportWrapper');
            const outputContent = document.getElementById('outputContent');
            const pdfBtn = document.getElementById('pdfBtn');

            loader.style.display = 'block';
            reportWrapper.style.display = 'none';
            pdfBtn.style.display = 'none';

            try {
                const response = await fetch('/summarize_pdf', {
                    method: 'POST',
                    body: formData // إرسال الملف الفعلي
                });

                const data = await response.json();
                
                if (data.result) {
                    outputContent.style.direction = "rtl";
                    outputContent.innerHTML = marked.parse(data.result);
                    reportWrapper.style.display = 'block';
                    pdfBtn.style.display = 'flex';
                    
                    updateUserPoints(15); // نقاط أعلى لتلخيص الملفات
                } else {
                    alert("حدث خطأ أثناء تلخيص الملف.");
                }
                
            } catch (error) {
                console.error("Upload Error:", error);
                alert("فشل الاتصال بالسيرفر لرفع الملف.");
            } finally {
                loader.style.display = 'none';
                // إعادة تصفير حقل الرفع للسماح برفع نفس الملف مرة أخرى إذا لزم الأمر
                pdfUpload.value = '';
            }
        });
    }
});

// --- وظائف مساعدة ---

// وظيفة تحديث النقاط
function updateUserPoints(newPoints) {
    const pointsElement = document.getElementById('userPoints');
    if (pointsElement) {
        pointsElement.innerText = parseInt(pointsElement.innerText) + newPoints;
    }
}

// وظيفة تصدير التقرير إلى ملف PDF (كودك القديم)
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    const options = {
        margin:       0.5,
        filename:     'AcademiX_Report.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().set(options).from(element).save();
}
