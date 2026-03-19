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
            // تفعيل وإظهار زر الحفظ
            const saveBtn = document.getElementById('pdfBtnReport');
            saveBtn.style.display = 'inline-flex';
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

// 2. دالة تنسيق المخرج (تدعم النصوص الطويلة جداً واللغتين)
function renderFormattedOutput(rawText) {
    const wrapper = document.getElementById('reportWrapper');
    const content = document.getElementById('outputContent');
    wrapper.style.display = 'block';

    // استخدام مكتبة marked لتحويل Markdown إلى HTML
    let htmlContent = marked.parse(rawText);

    content.innerHTML = `
        <div class="report-header" style="text-align:center; border-bottom:2px solid #4facfe; margin-bottom:20px; padding-bottom:10px;">
            <h1 style="color:#1e293b; font-family:'Cairo';">التقرير الأكاديمي الشامل</h1>
            <p style="color:#64748b;">AcademiX AI Professional Deep Analysis - 2026</p>
        </div>
        <div class="report-body" style="color: #1e293b; font-size: 1.1rem; line-height: 1.8;">
            ${htmlContent}
        </div>
    `;
    
    // التمرير بسلاسة إلى بداية النتيجة
    wrapper.scrollIntoView({ behavior: 'smooth' });
}

// 3. دالة حفظ الملف PDF (محسنة للملفات الطويلة جداً لضمان عدم ضياع التنسيق)
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    const btn = document.getElementById('pdfBtnReport');
    
    // تغيير حالة الزر للتفاعل مع المستخدم
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة الملف...';
    btn.disabled = true;

    const opt = {
        margin: [10, 10, 10, 10], // تقليل الهوامش للملخصات الطويلة
        filename: 'AcademiX_Full_Analysis.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2, 
            useCORS: true, 
            letterRendering: true,
            logging: false
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        // خاصية حيوية لضمان عدم تقطع النصوص الطويلة بين الصفحات
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        alert("تم حفظ الملف بنجاح!");
    }).catch(err => {
        console.error("PDF Export Error:", err);
        btn.innerHTML = originalText;
        btn.disabled = false;
        alert("فشل الحفظ، حاول مرة أخرى.");
    });
}

// 4. دالة تلخيص ملفات PDF (محدثة لدعم النتائج الطويلة جداً)
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
        if (data.summary) {
            renderFormattedOutput(data.summary);
            // إظهار زر الحفظ فوراً بعد انتهاء التلخيص
            const saveBtn = document.getElementById('pdfBtnReport');
            saveBtn.style.display = 'inline-flex';
        } else {
            alert("لم نتمكن من تلخيص الملف، جرب ملفاً آخر");
        }
    } catch (error) {
        console.error("PDF Error:", error);
        alert("فشل في معالجة الملف. تأكد من جودة النص داخل الـ PDF.");
    } finally {
        showLoader(false);
    }
}

// 5. وظيفة الـ Loader (المحسنة)
function showLoader(show) {
    const loader = document.getElementById('loader');
    const wrapper = document.getElementById('reportWrapper');
    const saveBtn = document.getElementById('pdfBtnReport');

    if (loader) loader.style.display = show ? 'block' : 'none';
    
    if (show) {
        wrapper.style.display = 'none';
        saveBtn.style.display = 'none';
    }
}
