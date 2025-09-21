/** @odoo-module **/
/**
 * Tệp này chịu trách nhiệm đăng ký widget p2p_dashboard_graph với hệ thống Odoo
 * Tách riêng việc đăng ký để đảm bảo nó xảy ra sau khi tất cả dependencies và component đã được tải
 */

import { registry } from "@web/core/registry";
import { P2PDashboardGraphField } from "./dashboard_graph_renderer_utf8";

// Đăng ký field widget với registry của Odoo (Odoo 18 expects a config object)
registry.category("fields").add("p2p_dashboard_graph", {
	component: P2PDashboardGraphField,
	// redundantly declare supported types here too; core uses this hint in some resolutions
	supportedTypes: ["json", "char", "text"],
});

// Debug helper
console.log("[P2P Dashboard] Widget registry loaded and widget registered successfully!");