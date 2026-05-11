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
let abortController = null;

function stopGeneration() {
    if (abortController) {
        abortController.abort();
    }
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && abortController) {
        stopGeneration();
    }
});

/**
 * On page load: check user config, populate UI, auto-generate
 */
function saveExtraInstructions() {
    localStorage.setItem('extraInstructions', document.getElementById('extraInstructions').value);
}

function saveStylePreference() {
    localStorage.setItem('stylePreference', document.getElementById('styleSelect').value);
}

function restoreGenerationPreferences() {
    const instructions = localStorage.getItem('extraInstructions') || '';
    const style = localStorage.getItem('stylePreference') || 'standard';
    document.getElementById('extraInstructions').value = instructions;
    document.getElementById('styleSelect').value = style;
}

function onLearningToggle() {
    const on = document.getElementById('learningToggle').checked;
    const label = document.getElementById('learningState');
    label.textContent = on ? 'On' : 'Off';
    label.classList.toggle('off', !on);
    localStorage.setItem('learningEnabled', on ? '1' : '0');
}

function getLearningEnabled() {
    const stored = localStorage.getItem('learningEnabled');
    return stored === null ? true : stored === '1';
}

document.addEventListener('DOMContentLoaded', async function () {
    restoreGenerationPreferences();

    // Restore learning toggle state
    const learningOn = getLearningEnabled();
    const toggle = document.getElementById('learningToggle');
    const label = document.getElementById('learningState');
    if (toggle) {
        toggle.checked = learningOn;
        if (label) {
            label.textContent = learningOn ? 'On' : 'Off';
            label.classList.toggle('off', !learningOn);
        }
    }
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

        // Auto-generate only if user has enabled the setting
        if (config.auto_generate && (subject || body)) {
            generateResponse(subject, senderName, senderEmail, body);
        }
    } catch (e) {
        console.warn('Could not check user config:', e);
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
        shared_mailbox_name: document.getElementById('setupSharedMailbox').value.trim(),
        auto_generate: document.getElementById('setupAutoGenerate').checked,
        ai_provider: document.getElementById('setupAiProvider').value
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

    // Hide setup modal and always show the import reminder for first-time users
    document.getElementById('setupModal').style.display = 'none';
    showImportReminder(true);
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
    hideStatus();

    const emailData = {
        subject: subject === '-' ? '' : subject,
        sender_name: senderName === '-' ? '' : senderName,
        sender_email: senderEmail === '-' ? '' : senderEmail,
        body: body,
        extra_instructions: document.getElementById('extraInstructions').value.trim(),
        style: document.getElementById('styleSelect').value
    };

    abortController = new AbortController();
    document.getElementById('stopBtn').style.display = 'inline-flex';

    try {
        const response = await fetch(`${API_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(emailData),
            signal: abortController.signal
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            const err = new Error(`API error: ${response.status}`);
            err.providerData = errData;
            throw err;
        }

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

        // Check if we should remind the user to re-import sent emails
        checkImportReminder();

    } catch (error) {
        if (error.name === 'AbortError') {
            // Silently cancelled — user clicked Stop or Esc, no message needed
            return;
        } else if (error.message.includes('Failed to fetch')) {
            showStatus('Cannot reach backend. Is the server running on port 5000?', 'error');
        } else if (error.providerData) {
            showProviderError(getProviderErrorMessage(error.providerData));
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
    } finally {
        abortController = null;
        document.getElementById('stopBtn').style.display = 'none';
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
    const rawText = document.getElementById('response').value;

    if (!rawText) {
        showStatus('No response to copy.', 'error');
        return;
    }

    // Extract [[annotations]] and strip them from the copied text
    const annotationRegex = /\[\[(.+?)\]\]/g;
    const annotations = [];
    let match;
    while ((match = annotationRegex.exec(rawText)) !== null) {
        annotations.push(match[1].trim());
    }
    const responseText = rawText.replace(annotationRegex, '').replace(/\n{3,}/g, '\n\n').trim();

    // Update the textarea with the cleaned text
    document.getElementById('response').value = responseText;

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

    // Send feedback (fire and forget), passing any extracted annotations
    sendFeedback(annotations);
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
function sendFeedback(annotations = []) {
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
            edit_notes: wasEdited ? 'User edited response' : '',
            annotations: annotations,
            learning_enabled: getLearningEnabled()
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
        document.getElementById('settingsUseSig').checked = config.use_signature === 1 || config.use_signature === true;
        document.getElementById('settingsSharedMailbox').value = config.shared_mailbox_name || '';
        document.getElementById('settingsAutoGenerate').checked = config.auto_generate === 1 || config.auto_generate === true;
        document.getElementById('settingsAiProvider').value = config.ai_provider || 'gemini';
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
        shared_mailbox_name: document.getElementById('settingsSharedMailbox').value.trim(),
        auto_generate: document.getElementById('settingsAutoGenerate').checked,
        ai_provider: document.getElementById('settingsAiProvider').value
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


/**
 * Post-generation reminder checks:
 * - If vector store is still empty after generating, show first-time call-to-action
 * - Every 10 generations, show a periodic nudge
 */
async function checkImportReminder() {
    try {
        const res = await fetch(`${API_URL}/api/stats`);
        const stats = await res.json();

        const total = stats.total_generated || 0;
        const vectorCount = stats.vector_store_count || 0;

        if (vectorCount === 0) {
            showImportReminder(true);
        } else if (total > 0 && total % 10 === 0) {
            showImportReminder(false);
        }
    } catch (e) {
        console.warn('Could not check stats for import reminder:', e);
    }
}

function showImportReminder(isFirstTime) {
    const modal = document.getElementById('importReminderModal');
    const msg = document.getElementById('importReminderMsg');

    if (isFirstTime) {
        msg.textContent = "Don't forget to import your sent emails! Click the \"Import Sent Emails\" button in your Outlook toolbar so the AI can learn from your past replies.";
    } else {
        msg.textContent = "You've generated 10 more responses. Consider clicking \"Import Sent Emails\" in your Outlook toolbar to keep the AI up to date with your latest sent emails.";
    }

    modal.style.display = 'flex';
}

function closeImportReminder() {
    document.getElementById('importReminderModal').style.display = 'none';
}

function getProviderErrorMessage({ provider, status_code }) {
    const name = {
        gemini: 'Google Gemini',
        groq: 'Groq',
        goa: 'GoA LLM Cluster',
        ollama: 'Ollama'
    }[provider] || 'The AI provider';

    if (status_code === 413) {
        return `Your request was too large for ${name}'s free tier token limit. Try again with a shorter email, or switch to a different provider in Settings.`;
    }
    if (status_code === 429) {
        return `${name} rate limit reached. Wait a moment and try again, or switch to a different provider in Settings.`;
    }
    if (status_code === 503) {
        if (provider === 'gemini') {
            return `Google Gemini is currently experiencing high demand. This is usually temporary — try again in a moment, or switch to a different provider in Settings.`;
        }
        return `${name} is temporarily unavailable. Try again shortly or switch providers in Settings.`;
    }
    if (status_code === 408) {
        return `${name} took too long to respond. It may be overloaded or offline. Try again or switch providers in Settings.`;
    }
    if (status_code === 401 || status_code === 403) {
        return `${name} rejected the request — authentication failed. Check your API key in Settings.`;
    }
    if (status_code === 404) {
        return `${name} endpoint not found. The URL or model name may have changed. Check your Settings.`;
    }
    if (provider === 'ollama') {
        return `Ollama failed to respond. Make sure Ollama is running on your machine, then try again.`;
    }
    return `${name} failed to respond. Check your connection or switch to a different provider in Settings.`;
}


function showProviderError(message) {
    document.getElementById('providerErrorMsg').textContent = message;
    document.getElementById('providerErrorModal').style.display = 'flex';
}

function closeProviderError() {
    document.getElementById('providerErrorModal').style.display = 'none';
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

// Ctrl+C nudge: if user presses Ctrl+C inside the response textarea,
// shake the Copy button to encourage using it (so feedback fires).
// Does NOT block or intercept the keypress — clipboard still works normally.
document.addEventListener('DOMContentLoaded', () => {
    const responseBox = document.getElementById('response');
    const copyBtn = document.getElementById('copyBtn');

    if (responseBox && copyBtn) {
        const copyLabel = copyBtn.querySelector('.copy-btn-label');
        responseBox.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'c' && copyLabel) {
                copyLabel.classList.remove('shake');
                void copyLabel.offsetWidth;
                copyLabel.classList.add('shake');
                copyLabel.addEventListener('animationend', () => {
                    copyLabel.classList.remove('shake');
                }, { once: true });
            }
        });
    }
});
