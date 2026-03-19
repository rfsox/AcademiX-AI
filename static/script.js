// استهداف العناصر مرة واحدة لضمان الأداء
const getEl = (id) => document.getElementById(id);

// --- الميزة الأولى: توليد التقارير الأكاديمية ---
async function generateReport() {
    const promptInput = getEl('promptInput');
    const outputContent = getEl('outputContent');
    const reportWrapper = getEl('reportWrapper');
    const loader = getEl('loader');
    const pdfBtn = getEl('pdfBtnReport'); // تأكد من الـ ID المحدث في HTML

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
            outputContent.innerHTML = marked.parse(data.result);
            reportWrapper.style.display = 'block';
            if(pdfBtn) pdfBtn.style.display = 'flex';
            
            updateUserPoints(10);
        } else {
            alert("حدث خطأ: " + (data.error || "نتيجة فارغة"));
        }
    } catch (error) {
        console.error("Error:", error);
        alert("خطأ في الاتصال، تأكد من رفع app.py بشكل صحيح على Vercel");
    } finally {
        loader.style.display = 'none';
    }
}

// --- الميزة الثانية: رفع وتلخيص PDF (النسخة العميقة والمزدوجة) ---
document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = getEl('pdfUpload');
    
    if (pdfUpload) {
        pdfUpload.addEventListener('change', async function() {
            const file = this.files[0];
            if (!file) return;

            if (file.type !== "application/pdf") {
                alert("يرجى اختيار ملف PDF فقط");
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            
            const loader = getEl('loader');
            const reportWrapper = getEl('reportWrapper');
            const output = getEl('outputContent');
            
            // تهيئة الواجهة لعملية طويلة
            loader.style.display = 'block';
            reportWrapper.style.display = 'none';

            try {
                const response = await fetch('/summarize_pdf', {
                    method: 'POST',
                    body: formData 
                });

                if (!response.ok) throw new Error("السيرفر استغرق وقتاً طويلاً أو حدث خطأ");

                const data = await response.json();
                
                if (data.result) {
                    // عرض النتيجة (إنجليزي + عربي) مع دعم الـ Markdown
                    output.innerHTML = marked.parse(data.result);
                    reportWrapper.style.display = 'block';
                    
                    // إظهار أزرار الحفظ المحدثة
                    const pdfBtn = getEl('pdfBtnReport');
                    if(pdfBtn) pdfBtn.style.display = 'flex';
                    
                    updateUserPoints(20); // نقاط أكثر للعمليات المعقدة
                } else {
                    alert("فشل التلخيص: " + data.result);
                }
            } catch (error) {
                console.error("Upload Error:", error);
                alert("حدث خطأ أثناء معالجة الملف العميق. حاول مع ملف أصغر إذا استمر الخطأ.");
            } finally {
                loader.style.display = 'none';
                pdfUpload.value = ''; 
            }
        });
    }
});

// --- وظيفة الحفظ المحدثة (تدعم الملفات الطويلة وتمنع قص الكلام) ---
function exportToPDF() {
    const element = getEl('reportWrapper');
    const pdfBtn = getEl('pdfBtnReport');

    if (!element) return;

    // إخفاء الزر مؤقتاً لكي لا يظهر في الـ PDF
    if(pdfBtn) pdfBtn.style.display = 'none';

    const opt = {
        margin:       [0.5, 0.5],
        filename:     'AcademiX_Summary_2026.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, letterRendering: true },
        jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' },
        pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] } // منع قص الفقرات بين الصفحات
    };

    html2pdf().set(opt).from(element).save().then(() => {
        if(pdfBtn) pdfBtn.style.display = 'flex';
    });
}

// تحديث النقاط في الواجهة
function updateUserPoints(pts) {
    const p = getEl('userPoints');
    if (p) {
        let currentPoints = parseInt(p.innerText) || 0;
        p.innerText = currentPoints + pts;
    }
}
