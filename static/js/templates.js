(function(window, undefined) {

    "use strict";

    var $ = window.jQuery,
        _ = window._;

    var Templates = window["Templates"] = {
        // Load templates
        templates: (function() {
            var templates = {};
            $("script[type='text/template']").each(function(index, template) {
              templates[$(template).data("name")] = _.template($(template).html());
            });
            return templates;
        })()
    };
    
})(window);
