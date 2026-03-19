// public/script.js

// 1. دالة توليد التقارير الأكاديمية (محدثة لتتوافق مع app.py)
async function generateReport() {
    const promptInput = document.getElementById('promptInput');
    const prompt = promptInput.value.trim();
    
    if (!prompt) return alert("الرجاء إدخال موضوع البحث");

    showLoader(true);
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();
        // التأكد من استلام المفتاح الصحيح 'report' من السيرفر
        if (data.report) {
            renderFormattedOutput(data.report);
            document.getElementById('pdfBtnReport').style.display = 'flex';
        } else {
            alert("حدث خطأ في استلام البيانات من السيرفر");
        }
    } catch (error) {
        console.error("خطأ في التوليد:", error);
        alert("حدث خطأ أثناء الاتصال بالسيرفر");
    } finally {
        showLoader(false);
    }
}

// 2. دالة تنسيق المخرج (تدعم الإنجليزية والعربية بذكاء)
function renderFormattedOutput(rawText) {
    const wrapper = document.getElementById('reportWrapper');
    const content = document.getElementById('outputContent');
    wrapper.style.display = 'block';

    // استخدام مكتبة marked لتحويل Markdown إلى HTML
    // ملاحظة: تأكد من استدعاء مكتبة marked في ملف index.html
    let htmlContent = marked.parse(rawText);

    content.innerHTML = `
        <div class="report-header" style="text-align:center; border-bottom:2px solid #4facfe; margin-bottom:20px; padding-bottom:10px;">
            <h1 style="color:#1e293b; font-family:'Cairo';">التقرير الأكاديمي الذكي</h1>
            <p style="color:#64748b;">AcademiX AI Professional Report - 2026</p>
        </div>
        <div class="report-body">
            ${htmlContent}
        </div>
    `;
    
    // سكرول تلقائي للنتيجة بحركة انسيابية
    wrapper.scrollIntoView({ behavior: 'smooth' });
}

// 3. دالة حفظ الملف PDF (إعدادات مطورة للغة العربية)
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    
    const opt = {
        margin: [10, 10, 10, 10],
        filename: 'AcademiX_Report.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2, 
            useCORS: true, 
            letterRendering: true,
            scrollX: 0,
            scrollY: 0
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // تشغيل عملية التحويل والحفظ
    html2pdf().set(opt).from(element).save();
}

// 4. دالة تلخيص ملفات PDF (محدثة لحل مشكلة الصورة رقم 7)
async function summarizePDF() {
    const fileInput = document.getElementById('pdfUpload');
    if (!fileInput || !fileInput.files[0]) return alert("يرجى اختيار ملف أولاً");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    showLoader(true);
    try {
        const response = await fetch('/summarize_pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error("Server Error");

        const data = await response.json();
        // السيرفر يرسل النتيجة بمفتاح 'summary'
        if (data.summary) {
            renderFormattedOutput(data.summary);
            document.getElementById('pdfBtnReport').style.display = 'flex';
        } else {
            alert("لم نتمكن من تلخيص الملف، جرب ملفاً آخر");
        }
    } catch (error) {
        console.error("PDF Error:", error);
        alert("فشل في معالجة الملف. تأكد أن الملف نصي وليس مجرد صور");
    } finally {
        showLoader(false);
    }
}

// 5. وظيفة الـ Loader
function showLoader(show) {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = show ? 'block' : 'none';
    if (show) {
        document.getElementById('reportWrapper').style.display = 'none';
        document.getElementById('pdfBtnReport').style.display = 'none';
    }
}
