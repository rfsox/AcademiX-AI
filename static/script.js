// public/script.js

// 1. دالة توليد التقارير الأكاديمية
async function generateReport() {
    const prompt = document.getElementById('promptInput').value;
    if (!prompt) return alert("الرجاء إدخال موضوع البحث");

    showLoader(true);
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();
        // تنسيق النص ليظهر بشكل (إنجليزي - عربي) مرتب
        renderFormattedOutput(data.report);
        document.getElementById('pdfBtnReport').style.display = 'flex';
    } catch (error) {
        console.error("خطأ في التوليد:", error);
        alert("حدث خطأ أثناء الاتصال بالسيرفر");
    } finally {
        showLoader(false);
    }
}

// 2. دالة تنسيق النص المخرج (عربي + إنجليزي مرتب)
function renderFormattedOutput(rawText) {
    const wrapper = document.getElementById('reportWrapper');
    const content = document.getElementById('outputContent');
    wrapper.style.display = 'block';

    // استخدام مكتبة marked لتحويل Markdown إلى HTML
    let htmlContent = marked.parse(rawText);

    // إضافة لمسة جمالية برمجية لتمييز الفقرات الإنجليزية عن العربية
    // نفترض أن النص المولد يأتي بتنسيق يسهل فصله أو فقرات متتالية
    content.innerHTML = `
        <div class="report-header" style="text-align:center; border-bottom:2px solid #4facfe; margin-bottom:20px; padding-bottom:10px;">
            <h1 style="color:#1e293b;">التقرير الأكاديمي الذكي</h1>
            <p style="color:#64748b;">تم التوليد بواسطة AcademiX AI - 2026</p>
        </div>
        <div class="report-body">
            ${htmlContent}
        </div>
    `;
    
    // سكرول تلقائي للنتيجة
    wrapper.scrollIntoView({ behavior: 'smooth' });
}

// 3. دالة حفظ الملف PDF (بجودة عالية وتنسيق صحيح)
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    
    // إعدادات المكتبة لضمان جودة الطباعة ودعم اللغة العربية
    const opt = {
        margin: [10, 10, 10, 10],
        filename: 'AcademiX_Report.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, letterRendering: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // تنفيذ عملية الحفظ
    html2pdf().set(opt).from(element).save();
}

// 4. وظائف المساعدة (Loader)
function showLoader(show) {
    document.getElementById('loader').style.display = show ? 'block' : 'none';
    if(show) document.getElementById('reportWrapper').style.display = 'none';
}

// 5. دالة تلخيص PDF (إذا كنت تستخدمها)
async function summarizePDF() {
    const fileInput = document.getElementById('pdfUpload');
    if (!fileInput.files[0]) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    showLoader(true);
    try {
        const response = await fetch('/summarize_pdf', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        renderFormattedOutput(data.summary);
        document.getElementById('pdfBtnReport').style.display = 'flex';
    } catch (error) {
        alert("فشل في تحليل ملف PDF");
    } finally {
        showLoader(false);
    }
}
