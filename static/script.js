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
    
    wrapper.scrollIntoView({ behavior: 'smooth' });
}

// 3. دالة حفظ الملف PDF (محسنة للملفات الطويلة جداً)
function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    const btn = document.getElementById('pdfBtnReport');
    
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة الملف...';
    btn.disabled = true;

    const opt = {
        margin: [10, 10, 10, 10],
        filename: 'AcademiX_Full_Analysis.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2, 
            useCORS: true, 
            letterRendering: true,
            logging: false
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
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

// 4. دالة تلخيص ملفات PDF
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
        
        const data = await response.json();
        if (data.summary) {
            renderFormattedOutput(data.summary);
            document.getElementById('pdfBtnReport').style.display = 'inline-flex';
        } else {
            alert("لم نتمكن من تلخيص الملف");
        }
    } catch (error) {
        console.error("PDF Error:", error);
        alert("حدث خطأ في معالجة الملف");
    } finally {
        showLoader(false);
    }
}

// --- 5. دالة توليد الأسئلة MCQ (تحديث جديد 8000 توكن) ---
async function generateMCQs() {
    const fileInput = document.getElementById('mcqFile'); // تأكد من وجود هذا الـ ID في ملف HTML
    if (!fileInput || !fileInput.files[0]) return alert("يرجى اختيار ملف المحاضرة أولاً");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    showLoader(true);
    try {
        const response = await fetch('/generate_mcq', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.questions) {
            // عرض الأسئلة المترجمة (إنجليزي/عربي) بنفس التنسيق الراقي
            renderFormattedOutput(data.questions);
            document.getElementById('pdfBtnReport').style.display = 'inline-flex';
        } else {
            alert("فشل في توليد الأسئلة");
        }
    } catch (error) {
        console.error("MCQ Error:", error);
        alert("حدث خطأ أثناء توليد الأسئلة");
    } finally {
        showLoader(false);
    }
}

// دالة تحديث اسم ملف الأسئلة عند الاختيار (للواجهة)
function updateMcqFileName(input) {
    if (input.files[0]) {
        document.getElementById('mcqFileName').innerHTML = `<b style="color: #f59e0b">جاهز:</b> ${input.files[0].name}`;
    }
}

// 6. وظيفة الـ Loader
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
