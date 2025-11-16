(function(){
  function initJsonEditorField(el){
    try {
      var opts = {};
      var dataAttr = el.getAttribute('data-jsoneditor-options');
      if (dataAttr) {
        opts = JSON.parse(dataAttr);
      } else if (el.options) {
        opts = el.options;
      }
      // create container
      var container = document.createElement('div');
      container.style.minHeight = '150px';
      el.style.display = 'none';
      el.parentNode.insertBefore(container, el.nextSibling);

      // convert initial value
      var initial = {};
      try {
        initial = JSON.parse(el.value || '{}' );
      } catch(e){
        initial = {};
      }

      var editor = new JSONEditor(container, opts);
      editor.set(initial);

      // write back on change / blur / submit
      var writeBack = function(){
        try {
          el.value = JSON.stringify(editor.get());
        } catch(e){
          // fallback: keep previous value
        }
      };
      // on submit of the form, ensure writeback
      var form = el.closest('form');
      if (form){
        form.addEventListener('submit', writeBack);
      }
      // also on blur/demand
      container.addEventListener('focusout', writeBack);
    } catch(err){
      console.error('jsoneditor init error', err);
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    var els = document.querySelectorAll('.json-editor');
    els.forEach(initJsonEditorField);
  });
})();