// استهداف العناصر مرة واحدة لضمان الأداء
const getEl = (id) => document.getElementById(id);

// --- الميزة الأولى: توليد التقارير الأكاديمية ---
async function generateReport() {
    const promptInput = getEl('promptInput');
    const outputContent = getEl('outputContent');
    const reportWrapper = getEl('reportWrapper');
    const loader = getEl('loader');
    const pdfBtn = getEl('pdfBtnReport');

    if (!promptInput.value.trim()) {
        alert("يرجى إدخال موضوع البحث!");
        return;
    }

    loader.style.display = 'block';
    reportWrapper.style.display = 'none';
    if(pdfBtn) pdfBtn.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: promptInput.value }),
        });

        const data = await response.json();
        
        if (data.result) {
            outputContent.innerHTML = marked.parse(data.result);
            reportWrapper.style.display = 'block';
            if(pdfBtn) pdfBtn.style.display = 'flex';
            updateUserPoints(10);
        } else {
            alert("حدث خطأ في التوليد");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("خطأ في الاتصال بالسيرفر");
    } finally {
        loader.style.display = 'none';
    }
}

// --- الميزة الثانية: رفع وتلخيص PDF (دالة موحدة) ---
async function summarizePDF() {
    const pdfUpload = getEl('pdfUpload');
    const file = pdfUpload.files[0];
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
    const pdfBtn = getEl('pdfBtnReport');

    loader.style.display = 'block';
    reportWrapper.style.display = 'none';

    try {
        const response = await fetch('/summarize_pdf', {
            method: 'POST',
            body: formData 
        });

        const data = await response.json();
        
        if (data.result) {
            output.innerHTML = marked.parse(data.result);
            reportWrapper.style.display = 'block';
            if(pdfBtn) pdfBtn.style.display = 'flex';
            updateUserPoints(20);
        } else {
            alert("فشل التلخيص: " + data.result);
        }
    } catch (error) {
        console.error("Upload Error:", error);
        alert("حدث خطأ أثناء معالجة الملف");
    } finally {
        loader.style.display = 'none';
        pdfUpload.value = ''; 
    }
}

// --- الميزة الثالثة: مصنع اختبارات MCQ (إضافة الميزة البرمجية) ---
async function generateMCQ() {
    const input = getEl('mcqInput');
    const topic = input.value.trim();
    if(!topic) return alert("أدخل موضوع الاختبار أولاً");

    const loader = getEl('loader');
    const output = getEl('outputContent');
    const reportWrapper = getEl('reportWrapper');

    loader.style.display = 'block';
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: `أنشئ اختبار اختيار من متعدد (MCQ) مفصل عن: ${topic}. مع ذكر الإجابات الصحيحة في النهاية.` }),
        });
        const data = await response.json();
        output.innerHTML = marked.parse(data.result);
        reportWrapper.style.display = 'block';
    } catch (e) {
        alert("خطأ في توليد الأسئلة");
    } finally {
        loader.style.display = 'none';
    }
}

// --- وظيفة الحفظ المحدثة ---
function exportToPDF() {
    const element = getEl('reportWrapper');
    const pdfBtn = getEl('pdfBtnReport');

    if (!element) return;
    if(pdfBtn) pdfBtn.style.display = 'none';

    const opt = {
        margin:       [0.5, 0.5],
        filename:     'AcademiX_Document_2026.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, letterRendering: true },
        jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' },
        pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        if(pdfBtn) pdfBtn.style.display = 'flex';
    });
}

function updateUserPoints(pts) {
    const p = getEl('userPoints');
    if (p) {
        let currentPoints = parseInt(p.innerText) || 0;
        p.innerText = currentPoints + pts;
    }
}
