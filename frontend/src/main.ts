const probeForm = document.getElementById('probe-form') as HTMLFormElement;
const targetInput = document.getElementById('target-input') as HTMLInputElement;
const resultsArea = document.getElementById('results-area') as HTMLDivElement;
const submitBtn = document.getElementById('submit-btn') as HTMLButtonElement;

probeForm.addEventListener('submit', async (e: Event) => {
    e.preventDefault();
    const target = targetInput.value.trim();
    if (!target) return;

    // Loading State
    submitBtn.disabled = true;
    submitBtn.innerText = "Probing Sequence Active...";
    resultsArea.innerHTML = `
        <div class="animate-pulse flex space-x-4 p-4 glass rounded-2xl">
            <div class="flex-1 space-y-3 py-1">
                <div class="h-2 bg-zinc-800 rounded"></div>
                <div class="grid grid-cols-3 gap-4">
                    <div class="h-2 bg-zinc-800 rounded col-span-2"></div>
                    <div class="h-2 bg-zinc-800 rounded col-span-1"></div>
                </div>
            </div>
        </div>`;
    
    try {
        const response = await fetch(`/api/cnnct?target=${encodeURIComponent(target)}`);
        
        if (!response.ok) {
            const errorMsg = response.status === 429 ? "Rate Limit Exceeded" : "Uplink Error";
            throw new Error(errorMsg);
        }

        const data = await response.json();
        renderModernResults(data);
    } catch (err) {
        resultsArea.innerHTML = `
            <div class="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl text-center text-sm">
                ${err instanceof Error ? err.message : 'Unknown system fault'}
            </div>`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Run Connectivity Test";
    }
});

function renderModernResults(data: any) {
    const statusIcon = (val: boolean) => val 
        ? '<span class="text-emerald-400 font-bold">ONLINE</span>' 
        : '<span class="text-rose-500 font-bold">OFFLINE</span>';

    resultsArea.innerHTML = `
        <div class="space-y-3">
            <div class="flex items-center justify-between p-4 bg-zinc-900/30 rounded-2xl border border-zinc-800/50">
                <span class="text-zinc-400 text-sm">Service Port 80 (HTTP)</span>
                ${statusIcon(data.tcp_80)}
            </div>
            <div class="flex items-center justify-between p-4 bg-zinc-900/30 rounded-2xl border border-zinc-800/50">
                <span class="text-zinc-400 text-sm">Secure Port 443 (HTTPS)</span>
                ${statusIcon(data.tcp_443)}
            </div>
            <div class="flex items-center justify-between p-4 bg-zinc-900/30 rounded-2xl border border-zinc-800/50">
                <span class="text-zinc-400 text-sm">HTTP Protocol Response</span>
                <span class="font-mono ${data.http_response === 200 ? 'text-indigo-400' : 'text-zinc-500'}">
                    ${data.http_response || '---'}
                </span>
            </div>
        </div>
    `;
}