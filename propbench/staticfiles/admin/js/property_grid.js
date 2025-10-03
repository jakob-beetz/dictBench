(function(){
// read config injected by template
const cfg = window.PropertyGridConfig || {};
const GRID_DATA_URL = cfg.GRID_DATA_URL || '/properties/api/grid-data/';
const DICTS_API_URL = cfg.DICTS_API_URL || '/properties/api/dictionaries/';

// Single global namespace to avoid redeclaration issues
window.PropertyGrid = window.PropertyGrid || {
    table: null,
    fuzzySearcher: null,
    undoStack: [],
    redoStack: [],
    currentEditingProperty: null,
    bulkSelectedRows: []
};

// Ensure updateLastModified exists to avoid "updateLastModified is not defined" errors
if (typeof window.updateLastModified === 'undefined') {
    window.updateLastModified = function() {
        // no-op fallback for grids that expect this function
        return;
    };
}

// Helper functions
function getCsrfToken() {
    if (cfg.CSRF_TOKEN) return cfg.CSRF_TOKEN;
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const cookie = document.cookie.split(';').map(c=>c.trim()).find(c=>c.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(show) {
    const container = document.querySelector('.property-grid-container');
    if (show) container.classList.add('loading'); else container.classList.remove('loading');
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `position: fixed; top: 20px; right: 20px; padding: 15px 20px; border-radius: 5px; color: white; font-weight: 500; z-index: 10000; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); animation: slideIn 0.3s ease;`;
    notification.style.background = type === 'success' ? '#28a745' : '#dc3545';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(()=>{ notification.style.animation = 'slideOut 0.3s ease'; setTimeout(()=>notification.remove(),300); }, 3000);
}
function showError(msg){ console.error(msg); showNotification(msg,'error'); }
function showSuccess(msg){ showNotification(msg,'success'); }

function populateDictionaryDropdowns(dictionaries) {
    const dictSelect = document.getElementById('dictionary');
    const bulkDictSelect = document.getElementById('bulk-dictionary');
    if (!dictSelect || !bulkDictSelect) return;
    dictSelect.innerHTML = '<option value="">Select dictionary...</option>';
    bulkDictSelect.innerHTML = '<option value="">Choose dictionary...</option>';
    const headerParams = { '': 'All' };
    dictionaries.forEach(d => {
        const value = d.guid || d.pk || d.id || '';
        const label = d.name || d.title || String(value);
        const opt = document.createElement('option'); opt.value = String(value); opt.textContent = label; dictSelect.appendChild(opt);
        const opt2 = opt.cloneNode(true); bulkDictSelect.appendChild(opt2);
        if (value) headerParams[String(value)] = label;
    });
    // update tabulator header filter params if table column exists
    try{
        const col = window.PropertyGrid.table.getColumn('dictionary_guid');
        if (col) col.updateDefinition({ headerFilterParams: { values: headerParams } });
    } catch(e) { console.warn('update header params failed', e); }
}

function initializeFuzzySearch() {
    if (window.Fuse) {
        const fuseOptions = { threshold: 0.4, keys: ['names','unit_of_measurement','data_type','status','dictionary_name'] };
        window.PropertyGrid.fuzzySearcher = new Fuse([], fuseOptions);
    }
}

function fuzzyFilter(headerValue, rowValue, rowData, filterParams) {
    if (!headerValue) return true;
    const names = String(rowValue || '');
    const filterValue = headerValue.toLowerCase();
    const searchValue = names.toLowerCase();
    let i=0; for (let c=0;c<filterValue.length && i<searchValue.length; c++){ if (filterValue[c]===searchValue[i]) i++; }
    return i===filterValue.length;
}

async function initializePropertyGrid() {
    if (typeof Tabulator === 'undefined') { document.getElementById('property-table').innerHTML = '<div class="alert alert-danger">Tabulator library failed to load</div>'; return; }
    window.PropertyGrid.table = new Tabulator('#property-table', {
        height: '500px',
        ajaxURL: GRID_DATA_URL,
        ajaxConfig: { credentials: 'same-origin', headers: { 'Accept': 'application/json' } },
        ajaxFiltering: true, ajaxSorting: true, ajaxProgressiveLoad: false,
        layout: 'fitColumns', responsiveLayout: 'collapse', placeholder: "No properties found. Click 'Add Property' to create your first property.",
        ajaxRequestFunc: async function(url, config, params){
            const table = window.PropertyGrid.table;
            const payload = { filters: table.getFilters(), sorters: table.getSorters(), search: (document.getElementById('global-search')||{}).value || '' };
            const finalUrl = url + '?' + new URLSearchParams({ payload: JSON.stringify(payload) });
            const resp = await fetch(finalUrl, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } });
            if (!resp.ok) { const t = await resp.text(); throw new Error(`HTTP ${resp.status}: ${t}`); }
            return resp.json();
        },
        ajaxResponse: function(url, params, response){ if (!response) return []; if (Array.isArray(response)) return response; if (response.properties && Array.isArray(response.properties)) return response.properties; if (response.data && Array.isArray(response.data)) return response.data; return []; },
        columns: [
            { title: 'Property Name', field: 'names', headerFilter:'input', headerFilterPlaceholder:'Search name...', headerFilterFunc: function(hv,rv,rd,fp){ if(!hv) return true; const names = rv||[]; const combined = names.map(n=>n.name).join(' '); return fuzzyFilter(hv,combined,rd,fp); }, formatter:function(cell){ const names = cell.getValue()||[]; if (names.length===0) return '<em class="text-muted">No name</em>'; const primary = names.find(n=>n.language==='en')||names[0]; return `<strong>${escapeHtml(primary.name)}</strong>`; }, width:250 },
            { title:'Data Type', field:'data_type', headerFilter:'list', headerFilterParams:{ values: {'':'All','string':'String','real':'Real','integer':'Integer','boolean':'Boolean'} }, formatter:function(cell){ const type = cell.getValue(); return type? type.charAt(0).toUpperCase()+type.slice(1):''; }, width:120 },
            { title:'Unit', field:'unit_of_measurement', headerFilter:'input', headerFilterPlaceholder:'Filter unit...', formatter:function(cell){ const unit = cell.getValue(); return unit? `<code>${escapeHtml(unit)}</code>`:'<em class="text-muted">No unit</em>'; }, width:100 },
            { title:'Status', field:'status', headerFilter:'list', headerFilterParams:{ values: {'':'All','active':'Active','draft':'Draft','deprecated':'Deprecated','withdrawn':'Withdrawn'} }, formatter:function(cell){ const status = cell.getValue(); return status? status.charAt(0).toUpperCase()+status.slice(1):''; }, width:100 },
            // Start with a simple input filter for Dictionary and upgrade to list once values are available
            { title:'Dictionary', field:'dictionary_guid', headerFilter:'input', headerFilterPlaceholder:'Filter dictionary...', formatter:function(cell){ const guidOrName = cell.getValue(); const nameFallback = cell.getRow().getData().dictionary_name; return guidOrName? escapeHtml(nameFallback||guidOrName) : (nameFallback? escapeHtml(nameFallback) : '<em class="text-muted">None</em>'); }, width:150 }
        ],
        dataLoaded:function(data){ const totalElement = document.getElementById('total-properties'); const filteredElement = document.getElementById('filtered-properties'); if (totalElement) totalElement.textContent = `Total: ${data.length}`; if (filteredElement) filteredElement.textContent = `Filtered: ${data.length}`; }
    });
}

function initializeEventListeners(){
    document.getElementById('global-search').addEventListener('input', function(e){ performGlobalSearch(e.target.value); });
    document.getElementById('clear-search').addEventListener('click', function(){ document.getElementById('global-search').value=''; document.getElementById('search-field').value=''; if (window.PropertyGrid.table) { window.PropertyGrid.table.clearFilter(); } });
    document.getElementById('search-field').addEventListener('change', function(){ const searchTerm = document.getElementById('global-search').value; if (searchTerm) performGlobalSearch(searchTerm); });
    document.getElementById('add-property').addEventListener('click', function(){ addNewProperty(); });
    document.getElementById('bulk-edit').addEventListener('click', function(){ openBulkEditModal(); });
    document.getElementById('export-data').addEventListener('click', function(){ exportData(); });
    document.getElementById('version-history').addEventListener('click', function(){ if ((window.PropertyGrid.bulkSelectedRows||[]).length===1) showVersionHistory(window.PropertyGrid.bulkSelectedRows[0].getData()); });
    document.getElementById('undo-last').addEventListener('click', function(){ performUndo(); });
    document.getElementById('redo-last').addEventListener('click', function(){ performRedo(); });
    initializeModalListeners();
}

function initializeModalListeners(){
    document.querySelectorAll('.modal .close').forEach(closeBtn=>{ closeBtn.addEventListener('click', function(){ closeModal(this.closest('.modal')); }); });
    document.querySelectorAll('.modal').forEach(modal=>{ modal.addEventListener('click', function(e){ if (e.target===modal) closeModal(modal); }); });
    document.getElementById('save-property').addEventListener('click', function(){ savePropertyForm(); });
    document.getElementById('cancel-edit').addEventListener('click', function(){ closeModal(document.getElementById('property-modal')); });
    document.getElementById('add-name').addEventListener('click', function(){ addPropertyNameField(); });
    document.querySelectorAll('.bulk-btn').forEach(btn=>{ btn.addEventListener('click', function(){ const action = this.getAttribute('data-action'); prepareBulkAction(action); }); });
    document.getElementById('apply-bulk').addEventListener('click', function(){ applyBulkChanges(); });
    document.getElementById('cancel-bulk').addEventListener('click', function(){ closeModal(document.getElementById('bulk-modal')); });
}

function initializeFuzzySearchInit(){
    if (window.Fuse){ const fuseOptions = { threshold:0.4, keys:[{name:'names', weight:0.3},{name:'unit_of_measurement', weight:0.2},{name:'data_type', weight:0.1},{name:'status', weight:0.1},{name:'dictionary_name', weight:0.2},{name:'physical_quantity_name', weight:0.1}] }; window.PropertyGrid.fuzzySearcher = new Fuse([], fuseOptions); }
}

function performGlobalSearch(searchTerm){ if (!searchTerm || !searchTerm.trim()){ if (window.PropertyGrid.table) { window.PropertyGrid.table.clearFilter(true); window.PropertyGrid.table.clearFilter(false); } return; } const searchField = document.getElementById('search-field').value; if (searchField){ if (window.PropertyGrid.table) window.PropertyGrid.table.setFilter(searchField, 'like', searchTerm); return; } const fuse = window.PropertyGrid.fuzzySearcher; if (!fuse){ console.warn('Fuzzy searcher not initialized'); return; } const results = fuse.search(searchTerm); const matchingIds = results.map(r=>r.item.guid||r.item.id||r.item.pk).filter(Boolean); if (window.PropertyGrid.table){ if (matchingIds.length>0){ window.PropertyGrid.table.setFilter(function(data){ const identifier = data.guid||data.id||data.pk; return matchingIds.includes(identifier); }); } else { window.PropertyGrid.table.setFilter(function(data){ const combined = [(data.names||[]).map(n=>n.name).join(' '), data.unit_of_measurement||'', data.data_type||'', data.status||'', data.dictionary_name||''].join(' '); return fuzzyFilter(searchTerm, combined, data, {}); }); } } }

// Data loading
async function loadInitialData(){ try{ showLoading(true); // fetch dictionaries only, table will request data via ajax
 const dictionariesResponse = await fetch(DICTS_API_URL, { credentials:'same-origin', headers:{ 'Accept':'application/json' } }); const dictText = await dictionariesResponse.text(); let dictionariesData = []; try{ dictionariesData = dictText ? JSON.parse(dictText) : []; }catch(e){ console.warn('Failed parsing dicts', e); dictionariesData = []; } populateDictionaryDropdowns(dictionariesData); if (window.PropertyGrid.table) await window.PropertyGrid.table.setData(); const tableData = window.PropertyGrid.table ? await window.PropertyGrid.table.getData() : []; if (window.PropertyGrid.fuzzySearcher && tableData.length>0) window.PropertyGrid.fuzzySearcher.setCollection(tableData); updateLastModified(); showLoading(false); showSuccess(`Loaded ${tableData.length} properties`); }catch(err){ console.error('Error loading initial data (ajax):', err); showError('Failed to load initial lookup data: '+err.message); showLoading(false); } }

// Expose minimal functions used elsewhere
window.PropertyGrid.getCsrfToken = getCsrfToken;
window.PropertyGrid.initializePropertyGrid = initializePropertyGrid;
window.PropertyGrid.initializeEventListeners = initializeEventListeners;

// Boot
document.addEventListener('DOMContentLoaded', function(){ initializeFuzzySearchInit(); initializePropertyGrid(); initializeEventListeners(); loadInitialData(); });

})();
