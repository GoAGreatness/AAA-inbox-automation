/**
 * Email Response Generator - Standalone Web App
 * Reads email data from URL parameters (passed by Outlook VBA macro)
 * No Office.js dependency - runs in Chrome
 */

const API_URL = 'https://localhost:5000';

// State
let currentResponseId = null;
let originalResponse = null;
let currentRating = null;

/**
 * On page load: check user config, populate UI, auto-generate
 */
document.addEventListener('DOMContentLoaded', async function () {
    const params = new URLSearchParams(window.location.search);

    const subject = params.get('subject') || '';
    const senderName = params.get('sender_name') || '';
    const senderEmail = params.get('sender_email') || '';
    const body = params.get('body') || '';

    // Populate email info
    document.getElementById('senderName').textContent = senderName || '-';
    document.getElementById('senderEmail').textContent = senderEmail || '-';
    document.getElementById('subject').textContent = subject || '-';

    // Check if user has been configured - show setup modal on first run
    try {
        const res = await fetch(`${API_URL}/api/user-config`);
        const config = await res.json();

        if (!config.full_name) {
            // First run - show setup modal before generating
            showSetupModal(subject, senderName, senderEmail, body);
            return;
        }
    } catch (e) {
        console.warn('Could not check user config:', e);
    }

    // Auto-generate if email data was passed in
    if (subject || body) {
        generateResponse(subject, senderName, senderEmail, body);
    }
});


/**
 * Show the first-run setup modal
 */
function showSetupModal(subject, senderName, senderEmail, body) {
    const modal = document.getElementById('setupModal');
    modal.style.display = 'flex';

    // Store email data so we can generate after setup
    modal.dataset.subject = subject;
    modal.dataset.senderName = senderName;
    modal.dataset.senderEmail = senderEmail;
    modal.dataset.body = body;
}


/**
 * Save setup config and proceed to generation
 */
async function saveSetup() {
    const fullName = document.getElementById('setupName').value.trim();
    if (!fullName) {
        alert('Please enter your full name.');
        return;
    }

    const config = {
        full_name: fullName,
        role: document.getElementById('setupRole').value.trim(),
        signature: document.getElementById('setupSignature').value.trim(),
        use_signature: document.getElementById('setupUseSig').checked,
        shared_mailbox_name: document.getElementById('setupSharedMailbox').value.trim()
    };

    try {
        await fetch(`${API_URL}/api/user-config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
    } catch (e) {
        console.error('Failed to save config:', e);
    }

    // Hide modal and proceed with generation
    const modal = document.getElementById('setupModal');
    modal.style.display = 'none';

    const subject = modal.dataset.subject;
    const senderName = modal.dataset.senderName;
    const senderEmail = modal.dataset.senderEmail;
    const body = modal.dataset.body;

    if (subject || body) {
        generateResponse(subject, senderName, senderEmail, body);
    }
}

/**
 * Generate AI response
 * Accepts optional params (from URL) or reads from UI
 */
async function generateResponse(subject, senderName, senderEmail, body) {
    // If called from button click, read from displayed values
    if (!subject) {
        subject = document.getElementById('subject').textContent;
        senderName = document.getElementById('senderName').textContent;
        senderEmail = document.getElementById('senderEmail').textContent;
        body = '';
    }

    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = '&#8987; Generating...';

    // Show loading animation
    document.getElementById('loadingText').classList.add('active');
    document.getElementById('loadingBar').classList.add('active');
    document.getElementById('responseSection').classList.remove('visible');
    hideStatus();

    const emailData = {
        subject: subject === '-' ? '' : subject,
        sender_name: senderName === '-' ? '' : senderName,
        sender_email: senderEmail === '-' ? '' : senderEmail,
        body: body
    };

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 1800000); // 30 min

        const response = await fetch(`${API_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(emailData),
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) throw new Error(`API error: ${response.status}`);

        const result = await response.json();

        // Store for feedback
        currentResponseId = result.response_id;
        originalResponse = result.generated_response;

        // Show response
        document.getElementById('response').value = result.generated_response;
        document.getElementById('responseMeta').textContent =
            `${(result.generation_time_ms / 1000).toFixed(1)}s  |  ${result.model}`;

        const similarCount = result.similar_emails_used || 0;
        const ragBadge = document.getElementById('ragBadge');
        if (similarCount > 0) {
            ragBadge.textContent = `${similarCount} similar emails used`;
            ragBadge.style.display = 'inline';
        } else {
            ragBadge.style.display = 'none';
        }

        document.getElementById('responseSection').classList.add('visible');
        showStatus('Response generated! Edit if needed, then copy.', 'success');

    } catch (error) {
        if (error.name === 'AbortError') {
            showStatus('Request timed out. Try again.', 'error');
        } else if (error.message.includes('Failed to fetch')) {
            showStatus('Cannot reach backend. Is the server running on port 5000?', 'error');
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
    } finally {
        btn.disabled = false;
        btn.innerHTML = '&#10024; Regenerate';
        document.getElementById('loadingText').classList.remove('active');
        document.getElementById('loadingBar').classList.remove('active');
    }
}

/**
 * Copy response to clipboard and send feedback
 */
async function copyResponse() {
    const responseText = document.getElementById('response').value;

    if (!responseText) {
        showStatus('No response to copy.', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(responseText);
    } catch {
        // Fallback
        document.getElementById('response').select();
        document.execCommand('copy');
    }

    const btn = document.getElementById('copyBtn');
    btn.innerHTML = '&#10003; Copied! Paste into Outlook';
    btn.classList.add('copied');

    setTimeout(() => {
        btn.innerHTML = '&#128203; Copy to Clipboard';
        btn.classList.remove('copied');
    }, 3000);

    // Send feedback (fire and forget)
    sendFeedback();
}

/**
 * Rate the response
 */
function rateResponse(rating) {
    currentRating = rating;

    const stars = document.querySelectorAll('.star');
    stars.forEach((star, index) => {
        star.classList.toggle('active', index < rating);
    });

    showStatus(`Rated ${rating}/5 — thank you!`, 'success');
}

/**
 * Send feedback to backend
 */
function sendFeedback() {
    if (!currentResponseId) return;

    const finalResponse = document.getElementById('response').value;
    const wasEdited = finalResponse !== originalResponse;

    fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            response_id: currentResponseId,
            final_response: finalResponse,
            was_edited: wasEdited,
            user_rating: currentRating || null,
            edit_notes: wasEdited ? 'User edited response' : ''
        })
    }).catch(err => console.error('Feedback error:', err));
}

/**
 * Open settings modal - pre-fills with current saved config
 */
async function openSettings() {
    try {
        const res = await fetch(`${API_URL}/api/user-config`);
        const config = await res.json();

        document.getElementById('settingsName').value = config.full_name || '';
        document.getElementById('settingsRole').value = config.role || '';
        document.getElementById('settingsSignature').value = config.signature || '';
        document.getElementById('settingsUseSig').checked = config.use_signature !== false;
        document.getElementById('settingsSharedMailbox').value = config.shared_mailbox_name || '';
    } catch (e) {
        console.error('Could not load settings:', e);
    }

    document.getElementById('settingsModal').style.display = 'flex';
}

function closeSettings() {
    document.getElementById('settingsModal').style.display = 'none';
}

/**
 * Save updated settings
 */
async function saveSettings() {
    const fullName = document.getElementById('settingsName').value.trim();
    if (!fullName) {
        alert('Please enter your full name.');
        return;
    }

    const config = {
        full_name: fullName,
        role: document.getElementById('settingsRole').value.trim(),
        signature: document.getElementById('settingsSignature').value.trim(),
        use_signature: document.getElementById('settingsUseSig').checked,
        shared_mailbox_name: document.getElementById('settingsSharedMailbox').value.trim()
    };

    try {
        await fetch(`${API_URL}/api/user-config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        closeSettings();
        showStatus('Settings saved!', 'success');
    } catch (e) {
        showStatus('Failed to save settings.', 'error');
    }
}


function showStatus(message, type) {
    const bar = document.getElementById('statusBar');
    bar.textContent = message;
    bar.className = `status-bar ${type}`;
    setTimeout(() => { bar.className = 'status-bar'; }, 5000);
}

function hideStatus() {
    document.getElementById('statusBar').className = 'status-bar';
}
