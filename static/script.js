// استهداف العناصر مرة واحدة لضمان الأداء
const getEl = (id) => document.getElementById(id);

// --- الميزة الأولى: توليد التقارير ---
async function generateReport() {
    const promptInput = getEl('promptInput');
    const outputContent = getEl('outputContent');
    const reportWrapper = getEl('reportWrapper');
    const loader = getEl('loader');
    const pdfBtn = getEl('pdfBtn');

    if (!promptInput.value.trim()) {
        alert("يرجى إدخال موضوع البحث!");
        return;
    }

    // تجهيز الواجهة للتحميل
    loader.style.display = 'block';
    reportWrapper.style.display = 'none';
    if(pdfBtn) pdfBtn.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: promptInput.value }),
        });

        if (!response.ok) throw new Error("فشل الاستجابة من السيرفر");

        const data = await response.json();
        
        if (data.result) {
            outputContent.style.direction = "rtl";
            // تحويل Markdown إلى HTML باستخدام مكتبة marked
            outputContent.innerHTML = marked.parse(data.result);
            
            reportWrapper.style.display = 'block';
            if(pdfBtn) pdfBtn.style.display = 'flex';
            
            updateUserPoints(10);
        } else {
            alert("حدث خطأ: " + (data.error || "نتيجة فارغة"));
        }
    } catch (error) {
        console.error("Error:", error);
        alert("خطأ في الاتصال بالسيرفر، تأكد من تشغيل app.py");
    } finally {
        loader.style.display = 'none';
    }
}

// --- الميزة الثانية: رفع وتلخيص PDF ---
document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = getEl('pdfUpload');
    
    if (pdfUpload) {
        pdfUpload.addEventListener('change', async function() {
            const file = this.files[0];
            if (!file) return;

            // التحقق من نوع الملف وحجمه (إضافة أمان)
            if (file.type !== "application/pdf") {
                alert("يرجى اختيار ملف PDF فقط");
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            
            const loader = getEl('loader');
            loader.style.display = 'block';

            try {
                const response = await fetch('/summarize_pdf', {
                    method: 'POST',
                    body: formData // إرسال كـ FormData
                });

                const data = await response.json();
                
                if (data.result) {
                    const output = getEl('outputContent');
                    output.style.direction = "rtl";
                    output.innerHTML = marked.parse(data.result);
                    getEl('reportWrapper').style.display = 'block';
                    if(getEl('pdfBtn')) getEl('pdfBtn').style.display = 'flex';
                    
                    updateUserPoints(15);
                } else {
                    alert("فشل التلخيص: " + data.result);
                }
            } catch (error) {
                console.error("Upload Error:", error);
                alert("حدث خطأ أثناء رفع ومعالجة الملف");
            } finally {
                loader.style.display = 'none';
                pdfUpload.value = ''; // تصفير الحقل لرفع ملف آخر لاحقاً
            }
        });
    }
});

// تحديث النقاط
function updateUserPoints(pts) {
    const p = getEl('userPoints');
    if (p) {
        let currentPoints = parseInt(p.innerText) || 0;
        p.innerText = currentPoints + pts;
    }
}

// تصدير PDF
function exportToPDF() {
    const element = getEl('reportWrapper');
    if (!element) return;

    const opt = {
        margin:       0.5,
        filename:     'AcademiX_Report.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();
}
