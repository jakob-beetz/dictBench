from django.forms.widgets import Textarea
from django.utils.safestring import mark_safe
import json

class JSONEditorWidget(Textarea):
    class Media:
        css = {
            'all': (
                'admin/vendor/jsoneditor/jsoneditor.min.css',
            )
        }
        js = (
            'admin/vendor/jsoneditor/jsoneditor.min.js',
        )

    def __init__(self, schema=None, mode='text', attrs=None):
        super().__init__(attrs=attrs)
        self.schema = schema
        self.mode = mode

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        textarea_id = attrs.get('id') or f'id_{name}'

        # ensure value is a JSON string
        try:
            if value is None or value == '':
                json_text = '{}'
            elif isinstance(value, str):
                # attempt to pretty-print
                parsed = json.loads(value) if value.strip() else {}
                json_text = json.dumps(parsed)
            else:
                json_text = json.dumps(value)
        except Exception:
            # fallback to raw string
            json_text = '{}'

        # render hidden textarea
        textarea_html = super().render(name, json_text, {**attrs, 'style': 'display:none;'}, renderer=renderer)

        container_id = f'{textarea_id}_jsoneditor'

        # prepare schema JS if present
        schema_js = json.dumps(self.schema) if self.schema else 'null'

        js = f"""
<div id="{container_id}" style="min-height:200px;border:1px solid #ddd;background:white;"></div>
<script>
(function(){{
    function tryParse(v){{
        try{{ return JSON.parse(v); }}catch(e){{ return null; }}
    }}
    var textarea = document.getElementById('{textarea_id}');
    var container = document.getElementById('{container_id}');
    var options = {{
        mode: '{self.mode}',
        modes: ['tree','view','form','code','text'],
        onChange: function(){{
            try{{
                var j = editor.get();
                textarea.value = JSON.stringify(j);
            }}catch(e){{
                // ignore invalid JSON in code mode
            }}
        }}
    }};

    // attach schema if provided
    if ({schema_js} !== null) {{
        options.schema = {schema_js};
    }}

    function init(){{
        if (!window.JSONEditor){{
            setTimeout(init, 50);
            return;
        }}
        try{{
            var startVal = tryParse(textarea.value) || {{}};
            // create editor instance scoped to this container
            var editor = new JSONEditor(container, options, startVal);
            // expose for debugging (scoped id)
            window['jsoneditor_' + '{textarea_id}'] = editor;
            // ensure textarea matches initial value
            try{{ textarea.value = JSON.stringify(editor.get()); }}catch(e){{}}
        }}catch(e){{
            console.error('JSONEditor init error', e);
        }}
    }}
    init();
}})();
</script>
"""

        return mark_safe(textarea_html + js)
