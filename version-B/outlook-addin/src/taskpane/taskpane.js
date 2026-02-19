/**
 * Email Response Generator - Task Pane Logic
 */

// Backend API URL
const API_URL = 'https://localhost:5000';

// Initialize Office.js
Office.initialize = function(reason) {
    console.log('Office.js initialized');

    // Load email information when ready
    $(document).ready(function() {
        loadEmailInfo();
    });
};

// Simple jQuery replacement
function $(selector) {
    if (selector === document) {
        return {
            ready: function(fn) {
                if (document.readyState !== 'loading') {
                    fn();
                } else {
                    document.addEventListener('DOMContentLoaded', fn);
                }
            }
        };
    }
    return document.querySelector(selector);
}

/**
 * Load current email information
 */
function loadEmailInfo() {
    const item = Office.context.mailbox.item;

    if (!item) {
        showStatus('No email selected', 'error');
        return;
    }

    // Display sender info
    if (item.from) {
        $('#senderName').textContent = item.from.displayName || '-';
        $('#senderEmail').textContent = item.from.emailAddress || '-';
    }

    // Display subject
    $('#subject').textContent = item.subject || '-';
}

/**
 * Generate AI response
 */
async function generateResponse() {
    const item = Office.context.mailbox.item;

    if (!item) {
        showStatus('No email selected', 'error');
        return;
    }

    // Disable button while generating
    const btn = $('#generateBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';

    try {
        // Get email body
        const body = await getEmailBody();

        // Prepare request data
        const emailData = {
            subject: item.subject || '',
            sender_name: item.from.displayName || '',
            sender_email: item.from.emailAddress || '',
            body: body
        };

        // Call backend API with timeout (AbortController - cancels request after set time)
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 120000); // 2 min timeout

        const response = await fetch(`${API_URL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(emailData),
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();

        // Show response section and display generated response
        $('#responseSection').className = 'response-section visible';
        $('#response').value = result.generated_response;
        $('#responseMeta').textContent = `${(result.generation_time_ms / 1000).toFixed(1)}s | ${result.model}`;

        // Store response ID for feedback
        window.currentResponseId = result.response_id;
        window.originalResponse = result.generated_response;

        showStatus('Response generated! Edit if needed, then insert.', 'success');

    } catch (error) {
        console.error('Error generating response:', error);

        if (error.name === 'AbortError') {
            showStatus('Request timed out - AI took too long. Try again.', 'error');
        } else if (error.message.includes('Failed to fetch')) {
            showStatus('Cannot reach backend. Is the server running?', 'error');
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.textContent = '✨ Generate Response';
    }
}

/**
 * Get email body text
 */
function getEmailBody() {
    return new Promise((resolve, reject) => {
        const item = Office.context.mailbox.item;

        item.body.getAsync(Office.CoercionType.Text, function(result) {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                resolve(result.value);
            } else {
                reject(new Error('Failed to get email body'));
            }
        });
    });
}

/**
 * Insert response into reply
 */
function insertResponse() {
    const responseText = $('#response').value;

    if (!responseText) {
        showStatus('No response to insert', 'error');
        return;
    }

    // Send feedback before inserting
    sendFeedback();

    const item = Office.context.mailbox.item;

    // Display reply form with generated response
    item.displayReplyForm({
        htmlBody: responseText.replace(/\n/g, '<br>')
    });

    showStatus('Response inserted into reply!', 'success');
}

/**
 * Copy response to clipboard
 */
function copyResponse() {
    const responseText = $('#response').value;

    if (!responseText) {
        showStatus('No response to copy', 'error');
        return;
    }

    navigator.clipboard.writeText(responseText).then(() => {
        showStatus('Copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        $('#response').select();
        document.execCommand('copy');
        showStatus('Copied to clipboard!', 'success');
    });
}

/**
 * Rate response (1-5 stars)
 */
function rateResponse(rating) {
    window.currentRating = rating;

    // Update star display
    const stars = document.querySelectorAll('.stars button');
    stars.forEach((star, index) => {
        star.className = index < rating ? 'active' : '';
    });

    showStatus(`Rated ${rating}/5 - feedback saved on insert`, 'success');
}

/**
 * Send feedback to backend
 * Tracks whether user edited the response and their rating
 */
function sendFeedback() {
    const finalResponse = $('#response').value;
    const wasEdited = finalResponse !== window.originalResponse;

    const feedbackData = {
        response_id: window.currentResponseId,
        final_response: finalResponse,
        was_edited: wasEdited,
        user_rating: window.currentRating || null,
        edit_notes: wasEdited ? 'User edited response' : ''
    };

    // Fire and forget - don't block insertion
    fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackData)
    }).catch(err => console.error('Feedback error:', err));
}

/**
 * Show status message
 */
function showStatus(message, type) {
    const status = $('#status');
    status.textContent = message;
    status.className = `status ${type}`;

    // Hide after 5 seconds
    setTimeout(() => {
        status.className = 'status';
    }, 5000);
}
