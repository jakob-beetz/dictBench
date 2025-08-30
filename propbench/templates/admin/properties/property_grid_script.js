// Continuation of property_grid.html JavaScript

// Version history functions
async function showVersionHistory(propertyData) {
    try {
        const response = await fetch(`/api/properties/${propertyData.id}/versions/`);
        const versions = await response.json();
        
        populateVersionHistory(versions);
        openModal(document.getElementById('version-history-modal'));
        
    } catch (error) {
        console.error('Error loading version history:', error);
        showError('Failed to load version history');
    }
}

function populateVersionHistory(versions) {
    const timeline = document.getElementById('version-timeline');
    timeline.innerHTML = '';
    
    versions.forEach((version, index) => {
        const versionEntry = document.createElement('div');
        versionEntry.className = 'version-entry';
        versionEntry.dataset.versionId = version.id;
        
        const changes = version.changes || {};
        const changeCount = Object.keys(changes).length;
        
        versionEntry.innerHTML = `
            <div class="version-info-left">
                <div class="version-date">${new Date(version.created_at).toLocaleString()}</div>
                <div class="version-user">Modified by: ${version.created_by || 'Unknown'}</div>
                <div class="version-changes">${changeCount} changes</div>
                ${version.comment ? `<div class="version-comment">${escapeHtml(version.comment)}</div>` : ''}
            </div>
            <div class="version-info-right">
                <div class="version-actions">
                    <button onclick="previewVersion(${version.id})" class="btn-sm btn-info">Preview</button>
                    <button onclick="compareVersions(${version.id})" class="btn-sm btn-warning">Compare</button>
                </div>
            </div>
        `;
        
        versionEntry.addEventListener('click', function() {
            selectVersion(this);
        });
        
        timeline.appendChild(versionEntry);
    });
}

function selectVersion(versionElement) {
    // Remove previous selection
    document.querySelectorAll('.version-entry.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Select new version
    versionElement.classList.add('selected');
    document.getElementById('restore-version').disabled = false;
}

async function restoreVersion() {
    const selectedVersion = document.querySelector('.version-entry.selected');
    if (!selectedVersion) return;
    
    const versionId = selectedVersion.dataset.versionId;
    
    if (!confirm('Are you sure you want to restore this version? Current changes will be lost.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/properties/restore-version/${versionId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('Version restored successfully');
            closeModal(document.getElementById('version-history-modal'));
            loadInitialData(); // Refresh grid
        } else {
            throw new Error('Restore failed');
        }
    } catch (error) {
        console.error('Restore error:', error);
        showError('Failed to restore version');
    }
}

// Bulk edit functions
function openBulkEditModal() {
    if (bulkSelectedRows.length === 0) {
        showError('Please select properties to edit');
        return;
    }
    
    document.getElementById('bulk-count').textContent = bulkSelectedRows.length;
    populateBulkDictionaries();
    openModal(document.getElementById('bulk-modal'));
}

async function populateBulkDictionaries() {
    try {
        const response = await fetch('/api/dictionaries/');
        const dictionaries = await response.json();
        
        const select = document.getElementById('bulk-dictionary');
        select.innerHTML = '<option value="">Choose dictionary...</option>';
        
        dictionaries.forEach(dict => {
            const option = document.createElement('option');
            option.value = dict.id;
            option.textContent = dict.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading dictionaries:', error);
    }
}

function prepareBulkAction(action) {
    const applyBtn = document.getElementById('apply-bulk');
    applyBtn.disabled = false;
    applyBtn.dataset.action = action;
    
    // Update button text based on action
    const actionTexts = {
        'activate': 'Activate All',
        'deprecate': 'Deprecate All',
        'draft': 'Mark as Draft',
        'move-dictionary': 'Move to Dictionary',
        'set-classification': 'Set Classification',
        'delete': 'Delete Selected'
    };
    
    applyBtn.textContent = actionTexts[action] || 'Apply Changes';
    
    if (action === 'delete') {
        applyBtn.className = 'btn btn-danger';
    } else {
        applyBtn.className = 'btn btn-primary';
    }
}

async function applyBulkChanges() {
    const action = document.getElementById('apply-bulk').dataset.action;
    const selectedIds = bulkSelectedRows.map(row => row.getData().id);
    
    let bulkData = { action: action, property_ids: selectedIds };
    
    // Add action-specific data
    switch (action) {
        case 'move-dictionary':
            const dictionaryId = document.getElementById('bulk-dictionary').value;
            if (!dictionaryId) {
                showError('Please select a dictionary');
                return;
            }
            bulkData.dictionary_id = dictionaryId;
            break;
            
        case 'set-classification':
            const classification = document.getElementById('bulk-classification').value;
            if (!classification.trim()) {
                showError('Please enter a classification reference');
                return;
            }
            bulkData.classification_reference = classification;
            break;
    }
    
    if (action === 'delete' && !confirm(`Are you sure you want to delete ${selectedIds.length} properties? This cannot be undone.`)) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/properties/bulk-edit/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(bulkData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(`Bulk operation completed: ${result.modified} properties updated`);
            closeModal(document.getElementById('bulk-modal'));
            loadInitialData(); // Refresh grid
            
            // Add to undo stack
            addToUndoStack({
                type: 'bulk_edit',
                action: action,
                property_ids: selectedIds,
                result: result,
                timestamp: new Date()
            });
        } else {
            throw new Error(result.error || 'Bulk operation failed');
        }
        
    } catch (error) {
        console.error('Bulk edit error:', error);
        showError('Bulk operation failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Form management functions
function populatePropertyForm(propertyData) {
    // Populate basic fields
    document.getElementById('data-type').value = propertyData.data_type || 'string';
    document.getElementById('unit-measurement').value = propertyData.unit_of_measurement || '';
    document.getElementById('status').value = propertyData.status || 'active';
    document.getElementById('value-domain').value = propertyData.value_domain || '';
    document.getElementById('classification').value = propertyData.classification_reference || '';
    
    // Populate dictionary dropdown
    if (propertyData.dictionary) {
        document.getElementById('dictionary').value = propertyData.dictionary;
    }
    
    // Populate physical quantity
    document.getElementById('physical-quantity').value = propertyData.physical_quantity_name || '';
    
    // Populate property names
    populatePropertyNames(propertyData.names || []);
    
    // Setup fuzzy search on form fields
    setupFormFuzzySearch();
}

function populatePropertyNames(names) {
    const container = document.getElementById('property-names-container');
    container.innerHTML = '';
    
    if (names.length === 0) {
        addPropertyNameField();
        return;
    }
    
    names.forEach(name => {
        addPropertyNameField(name.name, name.language);
    });
}

function addPropertyNameField(name = '', language = 'en') {
    const container = document.getElementById('property-names-container');
    const nameEntry = document.createElement('div');
    nameEntry.className = 'name-entry';
    
    nameEntry.innerHTML = `
        <input type="text" placeholder="Property name" value="${escapeHtml(name)}" class="name-input">
        <select class="language-select">
            <option value="en" ${language === 'en' ? 'selected' : ''}>EN</option>
            <option value="de" ${language === 'de' ? 'selected' : ''}>DE</option>
            <option value="fr" ${language === 'fr' ? 'selected' : ''}>FR</option>
            <option value="es" ${language === 'es' ? 'selected' : ''}>ES</option>
            <option value="it" ${language === 'it' ? 'selected' : ''}>IT</option>
        </select>
        <button type="button" onclick="removeNameField(this)">×</button>
    `;
    
    container.appendChild(nameEntry);
}

function removeNameField(button) {
    const container = document.getElementById('property-names-container');
    if (container.children.length > 1) {
        button.parentElement.remove();
    } else {
        showError('At least one property name is required');
    }
}

function setupFormFuzzySearch() {
    // Setup fuzzy search for units
    setupFieldFuzzySearch('unit-measurement', '/api/units/search/');
    
    // Setup fuzzy search for physical quantities
    setupFieldFuzzySearch('physical-quantity', '/api/physical-quantities/search/');
    
    // Setup fuzzy search for classifications
    setupFieldFuzzySearch('classification', '/api/classifications/search/');
}

function setupFieldFuzzySearch(fieldId, apiEndpoint) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    let searchTimeout;
    
    field.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value;
        
        if (query.length < 2) return;
        
        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`${apiEndpoint}?q=${encodeURIComponent(query)}`);
                const suggestions = await response.json();
                
                showFieldSuggestions(field, suggestions);
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300);
    });
}

function showFieldSuggestions(field, suggestions) {
    // Remove existing suggestions
    let existingSuggestions = field.parentElement.querySelector('.field-suggestions');
    if (existingSuggestions) {
        existingSuggestions.remove();
    }
    
    if (suggestions.length === 0) return;
    
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'field-suggestions';
    suggestionsDiv.style.cssText = `
        position: absolute;
        z-index: 1000;
        background: white;
        border: 1px solid #ccc;
        border-top: none;
        max-height: 200px;
        overflow-y: auto;
        width: 100%;
    `;
    
    suggestions.slice(0, 10).forEach(suggestion => {
        const suggestionItem = document.createElement('div');
        suggestionItem.className = 'suggestion-item';
        suggestionItem.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee;';
        suggestionItem.textContent = suggestion.value || suggestion.name || suggestion;
        
        suggestionItem.addEventListener('click', function() {
            field.value = this.textContent;
            suggestionsDiv.remove();
        });
        
        suggestionItem.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#f5f5f5';
        });
        
        suggestionItem.addEventListener('mouseout', function() {
            this.style.backgroundColor = '';
        });
        
        suggestionsDiv.appendChild(suggestionItem);
    });
    
    field.parentElement.style.position = 'relative';
    field.parentElement.appendChild(suggestionsDiv);
    
    // Remove suggestions when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function removeSuggestions(e) {
            if (!field.parentElement.contains(e.target)) {
                suggestionsDiv.remove();
                document.removeEventListener('click', removeSuggestions);
            }
        });
    }, 100);
}

async function savePropertyForm() {
    const formData = gatherFormData();
    
    if (!validateFormData(formData)) {
        return;
    }
    
    try {
        showLoading(true);
        
        const url = currentEditingProperty ? 
            `/api/properties/${currentEditingProperty.id}/` : 
            '/api/properties/';
        
        const method = currentEditingProperty ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(currentEditingProperty ? 'Property updated successfully' : 'Property created successfully');
            closeModal(document.getElementById('property-modal'));
            loadInitialData(); // Refresh grid
            
            // Add to undo stack
            addToUndoStack({
                type: currentEditingProperty ? 'edit' : 'create',
                property_id: result.id,
                old_data: currentEditingProperty,
                new_data: result,
                timestamp: new Date()
            });
        } else {
            throw new Error(result.error || 'Save failed');
        }
        
    } catch (error) {
        console.error('Save error:', error);
        showError('Failed to save property: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function gatherFormData() {
    // Gather property names
    const nameEntries = document.querySelectorAll('.name-entry');
    const names = Array.from(nameEntries).map(entry => ({
        name: entry.querySelector('.name-input').value.trim(),
        language: entry.querySelector('.language-select').value
    })).filter(name => name.name);
    
    return {
        names: names,
        data_type: document.getElementById('data-type').value,
        unit_of_measurement: document.getElementById('unit-measurement').value.trim(),
        status: document.getElementById('status').value,
        dictionary: document.getElementById('dictionary').value,
        physical_quantity_name: document.getElementById('physical-quantity').value.trim(),
        value_domain: document.getElementById('value-domain').value.trim(),
        classification_reference: document.getElementById('classification').value.trim()
    };
}

function validateFormData(formData) {
    if (formData.names.length === 0) {
        showError('At least one property name is required');
        return false;
    }
    
    if (!formData.dictionary) {
        showError('Dictionary selection is required');
        return false;
    }
    
    return true;
}

// Utility functions
function toggleRowSelection(row) {
    row.toggleSelect();
}

function updateSelectionUI() {
    const count = bulkSelectedRows.length;
    document.getElementById('selected-count').textContent = count;
    document.getElementById('selected-properties').textContent = `Selected: ${count}`;
    
    document.getElementById('bulk-edit').disabled = count === 0;
    document.getElementById('version-history').disabled = count !== 1;
}

function populateDictionaryDropdowns(dictionaries) {
    const selects = ['dictionary', 'bulk-dictionary'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options except first one
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        dictionaries.forEach(dict => {
            const option = document.createElement('option');
            option.value = dict.id;
            option.textContent = dict.name;
            select.appendChild(option);
        });
    });
}

function getPropertyDisplayName(propertyData) {
    if (propertyData.names && propertyData.names.length > 0) {
        const primary = propertyData.names.find(n => n.language === 'en') || propertyData.names[0];
        return primary.name;
    }
    return `Property ${propertyData.id}`;
}

// Undo/Redo functionality
function addToUndoStack(change) {
    undoStack.push(change);
    redoStack = []; // Clear redo stack when new change is made
    
    // Limit undo stack size
    if (undoStack.length > 50) {
        undoStack.shift();
    }
    
    updateUndoRedoButtons();
}

function performUndo() {
    if (undoStack.length === 0) return;
    
    const change = undoStack.pop();
    redoStack.push(change);
    
    // Apply reverse of the change
    applyReverseChange(change);
    updateUndoRedoButtons();
}

function performRedo() {
    if (redoStack.length === 0) return;
    
    const change = redoStack.pop();
    undoStack.push(change);
    
    // Reapply the change
    applyChange(change);
    updateUndoRedoButtons();
}

function updateUndoRedoButtons() {
    document.getElementById('undo-last').disabled = undoStack.length === 0;
    document.getElementById('redo-last').disabled = redoStack.length === 0;
}

async function applyReverseChange(change) {
    // Implementation depends on change type
    switch (change.type) {
        case 'cell_edit':
            // Reverse cell edit
            const row = propertyTable.getRowFromPosition(change.row);
            row.getCell(change.field).setValue(change.oldValue);
            break;
            
        case 'delete':
            // Restore deleted property
            await restoreDeletedProperty(change.data);
            break;
            
        case 'create':
            // Delete created property
            await deletePropertyById(change.property_id);
            break;
            
        // Add more cases as needed
    }
}

// Export functionality
function exportData() {
    const selectedData = bulkSelectedRows.length > 0 ? 
        bulkSelectedRows.map(row => row.getData()) : 
        propertyTable.getData();
    
    // Show export options
    const exportOptions = [
        { label: 'CSV', action: () => propertyTable.download("csv", "properties.csv") },
        { label: 'Excel', action: () => propertyTable.download("xlsx", "properties.xlsx") },
        { label: 'JSON', action: () => propertyTable.download("json", "properties.json") },
        { label: 'PDF', action: () => propertyTable.download("pdf", "properties.pdf") }
    ];
    
    showExportDialog(exportOptions);
}

function showExportDialog(options) {
    const dialog = document.createElement('div');
    dialog.className = 'export-dialog';
    dialog.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 1001;
    `;
    
    dialog.innerHTML = `
        <h3>Export Data</h3>
        <p>Choose export format:</p>
        <div class="export-options">
            ${options.map(option => 
                `<button class="btn btn-primary export-btn" data-format="${option.label}">${option.label}</button>`
            ).join('')}
        </div>
        <div style="margin-top: 15px;">
            <button class="btn btn-secondary" onclick="this.parentElement.parentElement.remove()">Cancel</button>
        </div>
    `;
    
    dialog.querySelectorAll('.export-btn').forEach((btn, index) => {
        btn.addEventListener('click', function() {
            options[index].action();
            dialog.remove();
        });
    });
    
    document.body.appendChild(dialog);
}

// Modal management
function openModal(modal) {
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
}

// Loading and notification functions
function showLoading(show) {
    const container = document.querySelector('.property-grid-container');
    if (show) {
        container.classList.add('loading');
    } else {
        container.classList.remove('loading');
    }
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.background = '#28a745';
    } else if (type === 'error') {
        notification.style.background = '#dc3545';
    }
    
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function updateLastModified() {
    const now = new Date();
    document.getElementById('last-modified').textContent = `Last modified: ${now.toLocaleString()}`;
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCsrfToken() {
    // Try multiple methods to get CSRF token
    let token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) return token.value;
    
    token = document.querySelector('meta[name="csrf-token"]');
    if (token) return token.getAttribute('content');
    
    // Try getting from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return value;
    }
    
    console.warn('CSRF token not found!');
    return '';
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .action-buttons {
        display: flex;
        gap: 5px;
        justify-content: center;
    }
    
    .btn-sm {
        padding: 4px 8px;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 28px;
        height: 28px;
    }
    
    .btn-sm.btn-primary { background: #007bff; color: white; }
    .btn-sm.btn-info { background: #17a2b8; color: white; }
    .btn-sm.btn-warning { background: #ffc107; color: #212529; }
    .btn-sm.btn-danger { background: #dc3545; color: white; }
    
    .btn-sm:hover { opacity: 0.8; }
    
    .lang-tag {
        background: #6c757d;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10px;
        text-transform: uppercase;
    }
    
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .badge-info {
        background: #17a2b8;
        color: white;
    }
    
    .text-muted {
        color: #6c757d !important;
    }
    
    .version-number {
        font-family: monospace;
        background: #e9ecef;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 12px;
    }
    
    .export-options {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 15px 0;
    }
    
    .field-suggestions {
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .suggestion-item:last-child {
        border-bottom: none;
    }
`;

document.head.appendChild(style);