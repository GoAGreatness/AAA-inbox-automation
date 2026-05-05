const API_URL = 'https://localhost:5000';

let ratingChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([
        loadStats(),
        loadPreferences(),
        loadLearningStats(),
        loadProviderStatus()
    ]);
});

async function loadStats() {
    try {
        const res = await fetch(`${API_URL}/api/stats`);
        const stats = await res.json();

        document.getElementById('vectorCount').textContent = stats.vector_store_count ?? stats.historical_emails ?? '—';
        document.getElementById('totalGenerated').textContent = stats.total_generated ?? '—';
        document.getElementById('avgRating').textContent = stats.avg_rating ? `${stats.avg_rating} / 5` : 'No ratings yet';
        document.getElementById('editRate').textContent = stats.edit_rate != null ? `${Math.round(stats.edit_rate * 100)}%` : '—';
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

async function loadPreferences() {
    const container = document.getElementById('chipList');
    try {
        const res = await fetch(`${API_URL}/api/preferences`);
        const prefs = await res.json();

        if (!prefs.length) {
            container.innerHTML = '<div class="empty-state">No preferences learned yet. Edit a generated response or add <strong>[[notes]]</strong> to teach the AI your style.</div>';
            return;
        }

        container.innerHTML = '';
        prefs.forEach(pref => {
            const chip = document.createElement('div');
            chip.className = 'chip';
            chip.dataset.id = pref.id;
            chip.innerHTML = `
                <span>${pref.note}</span>
                <button class="chip-delete" onclick="deletePreference(${pref.id}, this)" title="Remove">&#10005;</button>
            `;
            container.appendChild(chip);
        });
    } catch (e) {
        container.innerHTML = '<div class="empty-state">Could not load preferences.</div>';
    }
}

async function deletePreference(id, btn) {
    btn.disabled = true;
    try {
        const res = await fetch(`${API_URL}/api/preferences/${id}`, { method: 'DELETE' });
        if (res.ok) {
            const chip = document.querySelector(`.chip[data-id="${id}"]`);
            if (chip) chip.remove();

            // Show empty state if no chips left
            const remaining = document.querySelectorAll('.chip');
            if (!remaining.length) {
                document.getElementById('chipList').innerHTML = '<div class="empty-state">No preferences yet. Edit a generated response or add <strong>[[notes]]</strong> to teach the AI your style.</div>';
            }
        }
    } catch (e) {
        btn.disabled = false;
        console.error('Failed to delete preference:', e);
    }
}

async function loadLearningStats() {
    try {
        const res = await fetch(`${API_URL}/api/learning-stats`);
        const data = await res.json();
        renderRatingChart(data.daily || []);
    } catch (e) {
        console.error('Failed to load learning stats:', e);
    }
}

function renderRatingChart(daily) {
    const canvas = document.getElementById('ratingChart');
    const ctx = canvas.getContext('2d');

    const labels = daily.map(d => d.day);
    const ratings = daily.map(d => d.avg_rating);
    const counts = daily.map(d => d.generated_count);

    if (ratingChart) ratingChart.destroy();

    if (!daily.length) {
        ctx.font = '13px Segoe UI';
        ctx.fillStyle = '#aaa';
        ctx.textAlign = 'center';
        ctx.fillText('No data yet — generate some responses to see trends.', canvas.width / 2, 90);
        return;
    }

    ratingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Avg Rating',
                    data: ratings,
                    borderColor: '#0078d4',
                    backgroundColor: 'rgba(0,120,212,0.08)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointBackgroundColor: '#0078d4',
                    yAxisID: 'yRating'
                },
                {
                    label: 'Responses Generated',
                    data: counts,
                    borderColor: '#28a745',
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    borderDash: [4, 4],
                    pointRadius: 3,
                    pointBackgroundColor: '#28a745',
                    yAxisID: 'yCount'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { font: { family: 'Segoe UI', size: 12 }, boxWidth: 12 } }
            },
            scales: {
                yRating: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 5,
                    ticks: { font: { size: 11 } },
                    grid: { color: '#f0f0f0' }
                },
                yCount: {
                    type: 'linear',
                    position: 'right',
                    min: 0,
                    ticks: { font: { size: 11 }, stepSize: 1 },
                    grid: { display: false }
                },
                x: {
                    ticks: { font: { size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

async function loadProviderStatus() {
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusLabel');
    const nameEl = document.getElementById('providerName');
    const subEl = document.getElementById('providerSub');

    const providerNames = {
        gemini: 'Google Gemini',
        groq: 'Groq',
        goa: 'GoA LLM Cluster',
        ollama: 'Ollama (Local)'
    };

    try {
        const res = await fetch(`${API_URL}/api/health`);
        const data = await res.json();

        const provider = data.ai_provider || 'unknown';
        nameEl.textContent = providerNames[provider] || provider;
        subEl.textContent = `Active provider — selected in Settings`;

        dot.className = 'status-dot online';
        label.textContent = 'Reachable';
    } catch (e) {
        nameEl.textContent = 'Backend unreachable';
        subEl.textContent = 'Make sure the server is running on port 5000';
        dot.className = 'status-dot offline';
        label.textContent = 'Offline';
    }
}

async function confirmClearKnowledgeBase() {
    const confirmed = confirm('This will permanently delete all indexed emails from the knowledge base. The AI will lose all context from past emails.\n\nAre you sure?');
    if (!confirmed) return;

    try {
        const res = await fetch(`${API_URL}/api/clear-knowledge-base`, { method: 'POST' });
        if (res.ok) {
            document.getElementById('vectorCount').textContent = '0';
            alert('Knowledge base cleared.');
        } else {
            alert('Failed to clear knowledge base.');
        }
    } catch (e) {
        alert('Could not reach the backend.');
    }
}
