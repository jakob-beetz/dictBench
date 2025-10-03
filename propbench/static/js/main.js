// PropBench main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Format all JSON viewer elements
    document.querySelectorAll('.json-viewer').forEach(function(el) {
        try {
            const jsonData = JSON.parse(el.textContent);
            el.textContent = JSON.stringify(jsonData, null, 2);
        } catch (e) {
            console.error('Error parsing JSON:', e);
        }
    });

    // Pretty-print hidden/json-editor textareas (moved from base.html)
    document.querySelectorAll('.json-editor').forEach(function(el) {
        if (el.value) {
            try { el.value = JSON.stringify(JSON.parse(el.value), null, 2); } catch(e){}
        }
    });

    // Handle confirmation dialogs for dangerous actions
    document.body.addEventListener('htmx:confirm', function(evt) {
        // We can customize the confirmation dialog here
        if (evt.detail.question.includes('delete') || 
            evt.detail.question.includes('remove') || 
            evt.detail.question.includes('deprecate')) {
            evt.detail.isConfirmed = confirm(evt.detail.question);
        }
    });

    // Add a success message after successful HTMX requests
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (evt.detail.successful && evt.detail.xhr.status === 200 && !evt.detail.boosted) {
            const trigger = evt.detail.elt;
            if (trigger.hasAttribute('data-message')) {
                const message = trigger.getAttribute('data-message');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'alert alert-success alert-dismissible fade show';
                messageDiv.innerHTML = message + 
                    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
                
                const messagesContainer = document.getElementById('messages');
                if (messagesContainer) {
                    messagesContainer.appendChild(messageDiv);
                    // Auto-dismiss after 5 seconds
                    setTimeout(() => {
                        messageDiv.remove();
                    }, 5000);
                }
            }
        }
    });

    // Handle errors in HTMX requests
    document.body.addEventListener('htmx:responseError', function(evt) {
        const response = evt.detail.xhr.response;
        let errorMessage = 'An error occurred';
        
        try {
            const jsonResponse = JSON.parse(response);
            if (jsonResponse.detail) {
                errorMessage = jsonResponse.detail;
            } else if (jsonResponse.non_field_errors) {
                errorMessage = jsonResponse.non_field_errors.join(' ');
            } else {
                // Get the first error message from any field
                for (const field in jsonResponse) {
                    if (Array.isArray(jsonResponse[field])) {
                        errorMessage = `${field}: ${jsonResponse[field].join(' ')}`;
                        break;
                    }
                }
            }
        } catch (e) {
            // If not JSON, use the raw response if it's not too long
            if (response && response.length < 100) {
                errorMessage = response;
            }
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'alert alert-danger alert-dismissible fade show';
        messageDiv.innerHTML = errorMessage + 
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
        
        const messagesContainer = document.getElementById('messages');
        if (messagesContainer) {
            messagesContainer.appendChild(messageDiv);
        }
    });
});
