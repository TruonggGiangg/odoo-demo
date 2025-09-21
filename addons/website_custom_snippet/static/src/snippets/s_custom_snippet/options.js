/** @odoo-module */
import options from 'web_editor.snippets.options';

const CustomSnippetOptions = options.Class.extend({
    start: function () {
        // Custom logic khi snippet được chọn
        this._super.apply(this, arguments);
    },
    // Thêm các method custom nếu cần
});

options.registry.customSnippetOptions = CustomSnippetOptions;
export default CustomSnippetOptions;
