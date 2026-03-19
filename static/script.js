// 1. وظائف التنقل بين الأقسام (Show/Hide Sections)
function showSection(sectionName) {
    // إخفاء كل الأقسام
    document.getElementById('generate-section').style.display = 'none';
    document.getElementById('summarize-section').style.display = 'none';
    document.getElementById('result-area').style.display = 'none';

    // إزالة حالة النشاط من كل الأزرار
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));

    // إظهار القسم المطلوب وتفعيل الزر الخاص به
    if (sectionName === 'generate') {
        document.getElementById('generate-section').style.display = 'block';
        event.currentTarget.classList.add('active');
    } else if (sectionName === 'summarize') {
        document.getElementById('summarize-section').style.display = 'block';
        event.currentTarget.classList.add('active');
    } else if (sectionName === 'mcq') {
        document.getElementById('summarize-section').style.display = 'block'; // نستخدم نفس واجهة الرفع للملفات
        event.currentTarget.classList.add('active');
    }
}

// 2. وظيفة توليد التقارير (Generate Report)
async function generateReport() {
    const prompt = document.getElementById('report-prompt').value;
    if (!prompt) return alert("يرجى إدخال موضوع البحث أولاً");

    toggleLoader(true);
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await response.json();
        displayResult(data.report);
    } catch (error) {
        alert("حدث خطأ في الاتصال بالسيرفر");
    } finally {
        toggleLoader(false);
    }
}

// 3. وظيفة تلخيص الـ PDF (Summarize PDF)
async function summarizePDF() {
    const fileInput = document.getElementById('pdf-file');
    if (fileInput.files.length === 0) return alert("يرجى اختيار ملف PDF");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    toggleLoader(true);
    try {
        const response = await fetch('/summarize_pdf', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        displayResult(data.summary);
    } catch (error) {
        alert("خطأ في معالجة الملف");
    } finally {
        toggleLoader(false);
    }
}

// 4. عرض النتائج وتحويل الـ Markdown إلى HTML
function displayResult(content) {
    const resultArea = document.getElementById('result-area');
    const outputContent = document.getElementById('output-content');
    
    // استخدام مكتبة marked لتحويل النصوص الأكاديمية
    outputContent.innerHTML = marked.parse(content);
    
    resultArea.style.display = 'block';
    resultArea.scrollIntoView({ behavior: 'smooth' });
}

// 5. التحكم في شاشة التحميل (Loader)
function toggleLoader(show) {
    document.getElementById('loader').style.display = show ? 'flex' : 'none';
    if (show) {
        document.getElementById('result-area').style.display = 'none';
    }
}

// 6. وظيفة نسخ النص (Copy Content)
function copyResult() {
    const text = document.getElementById('output-content').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("تم نسخ النص بنجاح!");
    });
}

// 7. تحسين منطقة الرفع (Drop Zone Interaction)
const dropZone = document.querySelector('.drop-zone');
if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
        dropZone.style.background = 'rgba(99, 102, 241, 0.1)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--glass-border)';
        dropZone.style.background = 'transparent';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('pdf-file').files = files;
            alert("تم استلام الملف: " + files[0].name);
        }
    });
}
