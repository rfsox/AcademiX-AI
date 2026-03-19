// AcademiX Pro - Core Engine 2026

// إعدادات المكتبات (تأكد من تفعيل السطور الجديدة)
marked.setOptions({ 
    breaks: true, 
    gfm: true,
    headerIds: true
});

// 1. محرك توليد التقارير الأكاديمية
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
            renderFormattedOutput(data.report, "التقرير الأكاديمي الشامل");
            updateUserPoints(15); // إضافة نقاط للمستخدم
        } else {
            alert("حدث خطأ في استلام البيانات: " + (data.error || "خطأ مجهول"));
        }
    } catch (error) {
        console.error("Error:", error);
        alert("فشل الاتصال بالسيرفر الأكاديمي");
    } finally {
        showLoader(false);
    }
}

// 2. محرك الرؤية (حل الأسئلة بالصور) - إضافة جديدة
async function solveImage() {
    const fileInput = document.getElementById('imageUpload');
    if (!fileInput.files[0]) return alert("يرجى اختيار صورة أولاً");

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    showLoader(true);
    try {
        const response = await fetch('/analyze_image', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.solution) {
            renderFormattedOutput(data.solution, "تحليل وحل الصورة الذكي");
            updateUserPoints(20);
        } else {
            alert("فشل تحليل الصورة");
        }
    } catch (error) {
        alert("خطأ في معالجة الصورة");
    } finally {
        showLoader(false);
    }
}

// 3. تنسيق المخرجات (Markdown Engine)
function renderFormattedOutput(rawText, title) {
    const resultArea = document.getElementById('resultArea');
    const content = document.getElementById('outputContent');
    
    resultArea.style.display = 'block';

    // تحويل الماركدوان
    let htmlContent = marked.parse(rawText);

    content.innerHTML = `
        <div class="report-header" style="text-align:center; border-bottom:3px solid var(--primary); margin-bottom:30px; padding-bottom:15px;">
            <h1 style="color:var(--bg-dark); font-weight:900; font-size: 2rem;">${title}</h1>
            <p style="color:#64748b; font-size: 0.9rem;">AcademiX AI Global System © 2026</p>
        </div>
        <div class="markdown-body">
            ${htmlContent}
        </div>
    `;
    
    window.scrollTo({ top: resultArea.offsetTop - 50, behavior: 'smooth' });
}

// 4. نظام النقاط التفاعلي
function updateUserPoints(pts) {
    const pointsElement = document.getElementById('userPoints');
    if (pointsElement) {
        let currentPoints = parseInt(pointsElement.innerText);
        let newPoints = currentPoints + pts;
        
        // تحريك العداد
        let counter = currentPoints;
        let interval = setInterval(() => {
            if (counter >= newPoints) clearInterval(interval);
            pointsElement.innerText = counter;
            counter++;
        }, 50);
    }
}

// 5. حفظ الملف PDF (نسخة محسنة للجودة العالية)
function exportToPDF() {
    const element = document.getElementById('outputContent');
    const btn = document.querySelector('.action-btn.pdf');
    
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحضير...';

    const opt = {
        margin: 15,
        filename: 'AcademiX_Academic_File.pdf',
        image: { type: 'jpeg', quality: 1.0 },
        html2canvas: { scale: 3, useCORS: true, letterRendering: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        btn.innerHTML = originalContent;
    });
}

// 6. تلخيص PDF
async function summarizePDF() {
    const fileInput = document.getElementById('pdfUpload');
    if (!fileInput.files[0]) return alert("يرجى رفع ملف PDF أولاً");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    showLoader(true);
    try {
        const response = await fetch('/summarize_pdf', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.summary) {
            renderFormattedOutput(data.summary, "ملخص المحتوى الأكاديمي");
            updateUserPoints(10);
        }
    } catch (error) {
        alert("خطأ في قراءة ملف PDF");
    } finally {
        showLoader(false);
    }
}

// 7. وظائف واجهة المستخدم (UI)
function showLoader(show) {
    const loader = document.getElementById('loader');
    const resultArea = document.getElementById('resultArea');
    if (loader) loader.style.display = show ? 'flex' : 'none';
    if (show && resultArea) resultArea.style.display = 'none';
}

function copyText() {
    const text = document.getElementById('outputContent').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("تم نسخ النص بنجاح!");
    });
}

// معاينة الصور فور اختيارها
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('imagePreviewContainer').style.display = 'block';
            document.getElementById('imageStatusText').innerText = "تم التقاط الصورة بنجاح";
        }
        reader.readAsDataURL(input.files[0]);
    }
}
