(function(window, $){
  "use strict";

  window.initSelect2LibraryWidget = function(selector, autocompleteUrl) {
    const $el = $(selector);
    if (!$el.length) return;

    const libraries = $el.data('libraries') || '';
    const mode = $el.data('mode') || 'priority'; // 'union' or 'priority'

    $el.select2({
      ajax: {
        url: autocompleteUrl,
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term || '',
            libraries: libraries,
            mode: mode,
            page: params.page || 1,
          };
        },
        processResults: function(data, params) {
          params.page = params.page || 1;
          return {
            results: data.results || [],
            pagination: { more: (data.page && data.pages && data.page < data.pages) || false }
          };
        },
        cache: true
      },
      placeholder: $el.attr('placeholder') || 'Select…',
      minimumInputLength: 0,
      templateResult: function(item) { return item && item.text ? item.text : item; },
      templateSelection: function(item) { return item && item.text ? item.text : item; },
      escapeMarkup: function(markup){ return markup; }
    });

    // If a selected value exists in data-selected or as the <select> value, load it
    const initialId = $el.data('selected') || $el.val();
    if (initialId) {
      // ask endpoint for the specific id (you can support id param server-side)
      $.ajax({
        url: autocompleteUrl,
        data: { id: initialId, libraries: libraries },
        success: function(data) {
          if (data && data.results && data.results.length) {
            const it = data.results[0];
            const option = new Option(it.text, it.id, true, true);
            $el.append(option).trigger('change');
          }
        }
      });
    }
  };

})(window, jQuery);