(function(){
  window.initLibrarySelect2 = function(elSelector, ajaxUrl){
    var $el = $(elSelector);
    $el.select2({
      ajax: {
        url: ajaxUrl,
        data: function(params){ return { q: params.term, libraries: $el.data('libraries'), mode: $el.data('mode') || 'union' }; },
        processResults: function(data){ return { results: data.results, pagination: { more: data.page < data.pages } }; }
      },
      placeholder: $el.data('placeholder') || 'Select…',
      minimumInputLength: 0,
      templateResult: function(item){ return item ? item.text : ''; }
    });
  };
})();