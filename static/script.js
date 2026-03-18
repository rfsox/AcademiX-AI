/* static/js/script.js */
let points = 120;

async function generateReport() {
    const promptInput = document.getElementById('promptInput');
    const loader = document.getElementById('loader');
    const reportWrapper = document.getElementById('reportWrapper');
    const pdfBtn = document.getElementById('pdfBtn');
    const userPoints = document.getElementById('userPoints');
    const outputContent = document.getElementById('outputContent');
    const citations = document.getElementById('citations');

    const prompt = promptInput.value;
    if(!prompt) return alert("يرجى إدخال سؤالك!");

    loader.style.display = 'block';
    reportWrapper.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await response.json();
        
        if(data.result) {
            points += 10;
            userPoints.innerText = points;
            outputContent.innerHTML = marked.parse(data.result);
            
            citations.innerHTML = `
                <ul>
                    <li>Groq Cloud Academic Database (2026).</li>
                    <li>Llama-3.1 Knowledge Base Context.</li>
                    <li>Eng Reda Academic Platform.</li>
                </ul>
            `;

            reportWrapper.style.display = 'block';
            pdfBtn.style.display = 'flex';
        }
    } catch (e) {
        alert("حدث خطأ في الاتصال");
    } finally {
        loader.style.display = 'none';
    }
}

function exportToPDF() {
    const element = document.getElementById('reportWrapper');
    html2pdf().from(element).set({
        margin: 15,
        filename: 'AcademiX_Report_Pro.pdf',
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }).save();
}

// دعم الـ PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js');
    });
}