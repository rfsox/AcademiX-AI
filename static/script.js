// public/script.js

// 1. دالة توليد التقارير الأكاديمية
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
        if (data.report) {
            renderFormattedOutput(data.report);
            // إظهار زر الحفظ فوراً بعد النجاح
            document.getElementById('pdfBtnReport').style.display = 'inline-flex';
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

    // استخدام مكتبة marked لتحويل Markdown إلى HTML (تأكد من وجودها في index.html)
    let htmlContent = marked.parse(rawText);

    content.innerHTML = `
        <div class="report-header" style="text-align:center; border-bottom:2px solid #4facfe; margin-bottom:20px; padding-bottom:10px;">
            <h1 style="color:#1e293b; font-family:'Cairo';">التقرير الأكاديمي الذكي</h1>
            <p style="color:#64748b;">AcademiX AI Professional Analysis - 2026</p>
        </div>
        <div class="report-body" style="color: #1e293b;">
            ${htmlContent}
        </div>
    `;
    
    wrapper.scrollIntoView({ behavior: 'smooth' });
}

// 3. دالة حفظ الملف PDF المطورة (لحفظ الملخصات الطويلة جداً)
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    const btn = document.getElementById('pdfBtnReport');
    
    // تغيير شكل الزر أثناء الحفظ
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري إنشاء PDF...';
    btn.disabled = true;

    const opt = {
        margin: [15, 15, 15, 15],
        filename: 'AcademiX_Academic_Report.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2, 
            useCORS: true, 
            letterRendering: true,
            logging: false
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] } // لمنع تقطيع الصور والفقرات وسط الصفحة
    };

    html2pdf().set(opt).from(element).save().then(() => {
        // إعادة الزر لوضعه الطبيعي بعد انتهاء الحفظ
        btn.innerHTML = originalText;
        btn.disabled = false;
        alert("تم حفظ التقرير بنجاح!");
    }).catch(err => {
        console.error("PDF Export Error:", err);
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

// 4. دالة تلخيص ملفات PDF (محدثة لطلب ملخص طويل)
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
        
        if (!response.ok) throw new Error("خطأ في السيرفر");

        const data = await response.json();
        if (data.summary) {
            renderFormattedOutput(data.summary);
            // إظهار زر الحفظ عند انتهاء التلخيص
            document.getElementById('pdfBtnReport').style.display = 'inline-flex';
        } else {
            alert("لم نتمكن من تلخيص الملف، جرب ملفاً آخر");
        }
    } catch (error) {
        console.error("PDF Error:", error);
        alert("فشل في معالجة الملف. تأكد أن الملف نصي ومكتوب بشكل صحيح.");
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
