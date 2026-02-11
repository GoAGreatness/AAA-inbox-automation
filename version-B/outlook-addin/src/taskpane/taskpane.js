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

        // Call backend API
        const response = await fetch(`${API_URL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(emailData)
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();

        // Display generated response
        $('#response').value = result.generated_response;

        // Enable insert button
        $('#insertBtn').disabled = false;

        showStatus('Response generated successfully!', 'success');

    } catch (error) {
        console.error('Error generating response:', error);
        showStatus(`Error: ${error.message}`, 'error');
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

    const item = Office.context.mailbox.item;

    // Display reply form with generated response
    item.displayReplyForm({
        htmlBody: responseText.replace(/\n/g, '<br>')
    });

    showStatus('Response inserted into reply!', 'success');
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
