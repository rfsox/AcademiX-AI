// ميزة توليد التقارير
async function generateReport() {
    const promptInput = document.getElementById('promptInput');
    const outputContent = document.getElementById('outputContent');
    const reportWrapper = document.getElementById('reportWrapper');
    const loader = document.getElementById('loader');
    const pdfBtn = document.getElementById('pdfBtn');

    if (!promptInput.value) {
        alert("يرجى إدخال موضوع البحث!");
        return;
    }

    loader.style.display = 'block';
    reportWrapper.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: promptInput.value }),
        });
        const data = await response.json();
        if (data.result) {
            outputContent.style.direction = "rtl";
            outputContent.innerHTML = marked.parse(data.result);
            reportWrapper.style.display = 'block';
            pdfBtn.style.display = 'flex';
            updateUserPoints(10);
        }
    } catch (error) {
        alert("خطأ في الاتصال بالسيرفر");
    } finally {
        loader.style.display = 'none';
    }
}

// ميزة رفع وتلخيص PDF
document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = document.getElementById('pdfUpload');
    if (pdfUpload) {
        pdfUpload.addEventListener('change', async function() {
            const file = this.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('loader').style.display = 'block';

            try {
                const response = await fetch('/summarize_pdf', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.result) {
                    const output = document.getElementById('outputContent');
                    output.style.direction = "rtl";
                    output.innerHTML = marked.parse(data.result);
                    document.getElementById('reportWrapper').style.display = 'block';
                    updateUserPoints(15);
                }
            } catch (error) {
                alert("فشل رفع الملف");
            } finally {
                document.getElementById('loader').style.display = 'none';
                pdfUpload.value = '';
            }
        });
    }
});

function updateUserPoints(pts) {
    const p = document.getElementById('userPoints');
    if (p) p.innerText = parseInt(p.innerText) + pts;
}

function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    html2pdf().from(element).save('AcademiX_Report.pdf');
}
