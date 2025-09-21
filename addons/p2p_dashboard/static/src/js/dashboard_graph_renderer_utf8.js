/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useRef, onMounted, onPatched, onWillDestroy } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, xml } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
// Chart.js is optional. If present globally (window.Chart), we'll use it; otherwise we gracefully fallback.

/**
 * Text-based Dashboard Graph Field for P2P Dashboard
 * 
 * This widget renders statistics as text instead of charts
 */
export class P2PDashboardGraphField extends Component {
    static template = xml`
        <div class="o_field_dashboard_stats">
            <div class="p2p-stats-container" t-att-style="state.containerStyle">
                <!-- Runtime chart type selector (overrides XML options); hidden if opts.hideTypeSelector -->
                <div class="p2p-stats-controls" t-if="!state.opts.hideTypeSelector" style="display:flex; gap:8px; justify-content:flex-end; align-items:center; margin-bottom:8px;">
                    <label style="font-size:12px; color:#666;">Kiểu biểu đồ:</label>
                    <select t-model="state.userType" t-on-change="onTypeChange" style="font-size:12px; padding:4px 6px; border:1px solid #ccc; border-radius:4px;">
                        <option value="">Mặc định (bar)</option>
                        <option value="bar">Cột (bar)</option>
                        <option value="line">Đường (line)</option>
                        <option value="pie">Tròn (pie)</option>
                        <option value="doughnut">Vòng (doughnut)</option>
                        <option value="polarArea">Cực (polarArea)</option>
                        <option value="radar">Radar</option>
                    </select>
                </div>
                <h4 t-if="state.title" class="p2p-stats-title" t-esc="state.title"/>

                <!-- Loading state -->
                <div t-if="state.isLoading" class="p2p-stats-loading text-center p-4">
                    <i class="fa fa-spinner fa-spin fa-2x"/>
                    <p class="mt-2">Đang tải dữ liệu...</p>
                </div>

                <!-- Error state -->
                <div t-elif="state.hasError" class="p2p-stats-error text-center p-4 text-danger">
                    <i class="fa fa-exclamation-triangle fa-2x"/>
                    <p class="mt-2">Có lỗi xảy ra: <span t-esc="state.errorMessage || 'Không thể hiển thị dữ liệu'"/></p>
                </div>

                <!-- Empty data state -->
                <div t-elif="!state.chartData || !state.chartData.labels || state.chartData.labels.length === 0" class="p2p-stats-empty text-center p-4 text-muted">
                    <i class="fa fa-info-circle fa-2x"/>
                    <p class="mt-2"><t t-esc="props.name || 'Biểu đồ'"/><br/>Không có dữ liệu thống kê</p>
                </div>

                <!-- Chart display -->
                <div t-else="" class="p2p-chart-wrapper" t-att-style="state.chartAreaStyle">
                    <canvas t-ref="chartCanvas" style="width:100%; height:100%; display:block;"></canvas>
                </div>
            </div>
        </div>
    `;
    // Let Odoo know this widget is suitable for json/text fields
    static supportedTypes = ["json", "char", "text"];
    
    // Định nghĩa props cho component
    static props = {
        ...standardFieldProps,
        // field data type may be passed as 'type' by Odoo core; keep optional
        type: { type: String, optional: true },
        // ensure OWL forwards <field options="{...}">
        options: { type: Object, optional: true },
        nodeOptions: { type: Object, optional: true },
        attrs: { type: Object, optional: true },
    };

    setup() {
        if (this.env?.debug) console.log("[P2P Dashboard] Component setup started for:", this.props.name);
        // Lazily resolve Chart.js from global (if available)
        this._chartLib = this._resolveChartLib();
        // Internal guards/state
        this._chart = null;
        this._lastSignature = null; // signature of [rawFieldValue, chartType] to detect real changes
        this._notifiedNoChart = false; // avoid repeated state changes when Chart.js is missing
        this._rafId = null; // rAF scheduler id
        this._pendingRender = false; // coalesce renders in a frame
        this._resizeTimeout = null; // debounce resize observer
        
        // Kiểm tra xem props có hợp lệ không
        if (this.env?.debug) {
            if (!this.props.record) console.warn("[P2P Dashboard] Missing record in props");
            if (!this.props.name) console.warn("[P2P Dashboard] Missing field name in props");
        }
        
        // Ghi log thông tin quan trọng để debug
        if (this.env?.debug && this.props.field) {
            console.log("[P2P Dashboard] Field info:", {
                name: this.props.name,
                type: this.props.field.type,
                attrs: this.props.field.attrs
            });
        }
        
        // Khởi tạo state với useState để component tự động re-render khi state thay đổi
        this.state = useState({
            chartData: null,
            chartType: this._getChartType(),
            userType: "",
            opts: this._getWidgetOptions(),
            title: this._getTitle(),
            containerStyle: this._computeContainerStyle(),
            chartAreaStyle: this._computeChartAreaStyle(),
            isLoading: true,
            hasError: false,
            errorMessage: ""
        });
        this.canvasRef = useRef("chartCanvas");
        
        // Xử lý render ban đầu
        onMounted(() => {
            if (this.env?.debug) console.log("[P2P Dashboard] Component mounted!", this.props.name);
            try {
                const { chartData, chartType } = this._buildChartState();
                this.state.chartData = chartData;
                this.state.chartType = chartType;
                this.state.isLoading = false;
                this._lastSignature = this._computeSignature();
                this._scheduleRender();
                this._setupVisibilityWatcher();
            } catch (error) {
                console.error("[P2P Dashboard] Error during component mount:", error);
                this.state.hasError = true;
                this.state.errorMessage = error.message;
                this.state.isLoading = false;
            }
        });
        
        // Xử lý khi component được cập nhật
        onPatched(() => {
            if (this.env?.debug) console.log("[P2P Dashboard] Component patched!", this.props.name);
            try {
                const newSignature = this._computeSignature();
                if (newSignature !== this._lastSignature) {
                    const { chartData, chartType } = this._buildChartState();
                    // Only mutate state when something really changed
                    this.state.chartData = chartData;
                    // Respect user-selected override if any
                    this.state.chartType = this.state.userType || chartType;
                    this.state.opts = this._getWidgetOptions();
                    this.state.containerStyle = this._computeContainerStyle();
                    this.state.chartAreaStyle = this._computeChartAreaStyle();
                    this._lastSignature = newSignature;
                    this._scheduleRender();
                    this._setupVisibilityWatcher();
                } else {
                    // No data/type change; if chart not created yet (likely because canvas ref wasn't ready on mount), try to render now.
                    if (!this._chart) {
                        this._scheduleRender();
                        this._setupVisibilityWatcher();
                    } else if (typeof this._chart.resize === 'function') {
                        // Chart exists: allow resize if needed
                        try { this._chart.resize(); } catch (_) {}
                    }
                }
            } catch (error) {
                console.error("[P2P Dashboard] Error during component patch:", error);
                this.state.hasError = true;
                this.state.errorMessage = error.message;
            }
        });

        onWillDestroy(() => {
            if (this._chart) {
                this._chart.destroy();
                this._chart = null;
            }
            if (this._resizeObserver) {
                try { this._resizeObserver.disconnect(); } catch (_) {}
                this._resizeObserver = null;
            }
            if (this._rafId) {
                try { cancelAnimationFrame(this._rafId); } catch (_) {}
                this._rafId = null;
            }
            if (this._resizeTimeout) {
                clearTimeout(this._resizeTimeout);
                this._resizeTimeout = null;
            }
        });
    }

    onTypeChange(ev) {
        const val = (ev?.target?.value || '').trim();
        this.state.userType = val; // "" means default
        // Update chart type immediately and rerender
        const baseType = this._getChartType();
        this.state.chartType = this.state.userType || baseType || 'bar';
        this._scheduleRender();
    }

    _getWidgetOptions() {
        // Merge options from multiple sources
        const out = {};
        const merge = (obj) => {
            if (!obj || typeof obj !== 'object') return;
            for (const k of Object.keys(obj)) {
                if (obj[k] === undefined) continue;
                out[k] = obj[k];
            }
        };
        try {
            if (this.props.options && typeof this.props.options === 'object') merge(this.props.options);
            if (this.props.nodeOptions && typeof this.props.nodeOptions === 'object') merge(this.props.nodeOptions);
            if (this.props.field && this.props.field.nodeOptions && typeof this.props.field.nodeOptions === 'object') merge(this.props.field.nodeOptions);
            const a = this.props.attrs || {};
            if (typeof a.options === 'string') {
                try { merge(this._parseOptionsString(a.options)); } catch (_) {}
            } else if (a.options && typeof a.options === 'object') {
                merge(a.options);
            }
        } catch (_) {}
        return out;
    }

    _computeContainerStyle() {
        const opts = this._getWidgetOptions();
        const bg = opts.bg || '#f9f9f9';
        const border = opts.border || '#ddd';
        const padding = opts.padding || 15;
        const radius = opts.radius || 6;
        // Container should wrap header + controls + chart area without clipping
        return `border: 1px solid ${border}; padding: ${padding}px; border-radius: ${radius}px; background-color: ${bg};`;
    }

    _computeChartAreaStyle() {
        const opts = this._getWidgetOptions();
        const height = Number(opts.height) || 320;
        // Dedicated stable area for the canvas; prevents layout jump when switching types
        return `position:relative; width:100%; height:${height}px; overflow:hidden;`;
    }

    _scheduleRender() {
        if (this._pendingRender) return;
        this._pendingRender = true;
        this._rafId = requestAnimationFrame(() => {
            this._pendingRender = false;
            try { this._renderChart(); } catch (e) { console.error(e); }
        });
    }

    _setupVisibilityWatcher() {
        const el = this.canvasRef?.el;
        if (!el || typeof window === 'undefined') return;
        // Timed retry if element has no size yet
        const tryRenderIfVisible = (attempt = 0) => {
            if (!this.canvasRef?.el) return;
            const rect = this.canvasRef.el.getBoundingClientRect();
            if (rect.width > 10 && rect.height > 10) {
                // ensure chart sync with actual size
                if (this._chart && typeof this._chart.resize === 'function') {
                    try { this._chart.resize(); } catch (_) {}
                } else {
                    this._scheduleRender();
                }
                return;
            }
            if (attempt < 10) {
                setTimeout(() => tryRenderIfVisible(attempt + 1), 200);
            }
        };
        tryRenderIfVisible(0);

        // Observe size changes and refresh chart once when becomes visible
        if (typeof ResizeObserver !== 'undefined' && !this._resizeObserver) {
            this._resizeObserver = new ResizeObserver((entries) => {
                // Debounce to avoid thrashing
                if (this._resizeTimeout) clearTimeout(this._resizeTimeout);
                this._resizeTimeout = setTimeout(() => {
                    for (const entry of entries) {
                        const cr = entry.contentRect || {};
                        if ((cr.width || 0) > 10 && (cr.height || 0) > 10) {
                            if (this._chart && typeof this._chart.resize === 'function') {
                                try { this._chart.resize(); } catch (_) {}
                            } else {
                                this._scheduleRender();
                            }
                        }
                    }
                }, 100);
            });
            try {
                this._resizeObserver.observe(el);
            } catch (_) {}
        }
    }
    
    /**
     * Xử lý dữ liệu biểu đồ từ props và cập nhật state
     */
    _buildChartState() {
        // Xây dựng chartData và chartType nhưng KHÔNG đụng vào this.state ở đây
        const chartData = this._getChartData();
        const chartType = this._getChartType();
        // Apply user-selected type override if set
        const effectiveType = this.state?.userType || chartType;
        if (this.env?.debug) console.log("[P2P Dashboard] Processing data for", this.props.name, "type:", effectiveType);

        if (!chartData || !Array.isArray(chartData.labels)) {
            if (this.env?.debug) console.warn("[P2P Dashboard] Invalid or missing chart data/labels:", chartData);
            return { chartData: null, chartType: effectiveType };
        }

        if (!Array.isArray(chartData.datasets) || chartData.datasets.length === 0) {
            if (this.env?.debug) console.warn("[P2P Dashboard] Invalid chart data - missing or invalid datasets:", chartData);
            return { chartData: null, chartType: effectiveType };
        }

        // Chuẩn hóa datasets
        chartData.datasets.forEach((dataset, index) => {
            if (!Array.isArray(dataset.data)) {
                dataset.data = new Array(chartData.labels.length).fill(0);
            }
            if (dataset.data.length < chartData.labels.length) {
                if (this.env?.debug) console.warn(`[P2P Dashboard] Dataset ${index} has fewer data points than labels. Padding with zeros.`);
                dataset.data = [...dataset.data, ...new Array(chartData.labels.length - dataset.data.length).fill(0)];
            }
        });

        if (this.env?.debug) console.log("[P2P Dashboard] Chart data processed successfully:", {
            type: chartType,
            labels: chartData.labels.length,
            datasets: chartData.datasets.length
        });
    return { chartData, chartType: effectiveType };
    }

    /**
     * Render Chart.js chart
     */
    _renderChart() {
        if (!this.canvasRef || !this.canvasRef.el || !this.state.chartData || !this.state.chartData.labels) {
            return;
        }
        // If Chart.js not available, toggle error state ONCE and return
        if (!this._chartLib) {
            if (!this._notifiedNoChart) {
                this.state.hasError = true;
                this.state.errorMessage = "Thiếu thư viện Chart.js";
                this._notifiedNoChart = true;
            }
            return;
        }
        const Chart = this._chartLib;
        if (this.env?.debug) {
            try {
                console.log("[P2P Dashboard] Chart.js detected:", {
                    version: Chart?.version,
                    hasRegisterables: !!Chart?.registerables,
                    registerablesCount: Chart?.registerables?.length,
                });
            } catch (_) {}
        }
        const canvasEl = this.canvasRef.el;
        // Ensure the canvas intrinsic size matches the parent container to avoid small default fallback
        try {
            const parent = canvasEl.parentElement;
            if (parent) {
                const rect = parent.getBoundingClientRect();
                // Set HTML attributes (not just CSS) to control rendering resolution
                if (rect.width && rect.height) {
                    canvasEl.width = Math.max(1, Math.floor(rect.width));
                    canvasEl.height = Math.max(1, Math.floor(rect.height));
                }
                // Also make sure CSS reflects 100% fill
                canvasEl.style.width = '100%';
                canvasEl.style.height = '100%';
                canvasEl.style.display = 'block';
            }
        } catch (_) { /* ignore sizing errors */ }
        const ctx = canvasEl.getContext('2d');
        if (!ctx) {
            if (this.env?.debug) console.warn('[P2P Dashboard] Canvas 2D context not available');
            return;
        }
        if (this.env?.debug) {
            try {
                console.log('[P2P Dashboard] Canvas sizing:', {
                    cssWidth: canvasEl.style?.width,
                    cssHeight: canvasEl.style?.height,
                    attrWidth: canvasEl.width,
                    attrHeight: canvasEl.height,
                    rect: canvasEl.getBoundingClientRect?.(),
                });
            } catch (_) {}
        }
        const chartType = this.state.chartType || 'bar';
        const cfg = this._getWidgetOptions();
        const labels = this.state.chartData.labels;
        const datasets = (this.state.chartData.datasets || []).map((ds, idx) => {
            // Coerce data to numbers to avoid silent parsing issues
            const values = Array.isArray(ds.data) ? ds.data.map(v => {
                const n = Number(v);
                return Number.isFinite(n) ? n : 0;
            }) : [];
            const colors = this._getDatasetColors(ds.data?.length || labels.length, idx);
            const effectiveType = ds.type || chartType; // allow mixed charts per-dataset
            const isPieLike = ['pie','doughnut','polarArea'].includes(effectiveType);
            const isLineLike = effectiveType === 'line';

            // Gradient fill for line if requested
            let backgroundColor = ds.backgroundColor;
            if (!backgroundColor) {
                if (isPieLike) {
                    backgroundColor = colors.background;
                } else if (isLineLike && (cfg.fill === true || cfg.area === true || ds.fill === true)) {
                    try {
                        const gradCtx = this.canvasRef.el.getContext('2d');
                        const gradient = gradCtx.createLinearGradient(0, 0, 0, this.canvasRef.el.clientHeight || 320);
                        const base = colors.background[0] || '#4e79a7';
                        gradient.addColorStop(0, this._withAlpha(base, 0.35));
                        gradient.addColorStop(1, this._withAlpha(base, 0.05));
                        backgroundColor = gradient;
                    } catch (_) {
                        backgroundColor = colors.background[0];
                    }
                } else {
                    backgroundColor = colors.background[0];
                }
            }
            return {
                label: ds.label || `Dataset ${idx + 1}`,
                data: values,
                type: ds.type,
                backgroundColor,
                borderColor: ds.borderColor || (isPieLike ? colors.border : colors.border[0]),
                borderWidth: ds.borderWidth ?? (isLineLike ? 2 : 1),
                fill: isLineLike ? (ds.fill ?? (cfg.fill === true || cfg.area === true)) : undefined,
                tension: isLineLike ? (Number(cfg.smooth) || 0.35) : undefined,
                borderRadius: ds.borderRadius ?? (effectiveType === 'bar' ? (cfg.borderRadius ?? 6) : undefined),
                pointRadius: isLineLike ? (ds.pointRadius ?? 2) : undefined,
                pointHoverRadius: isLineLike ? (ds.pointHoverRadius ?? 4) : undefined,
                maxBarThickness: effectiveType === 'bar' ? (cfg.maxBarThickness ?? undefined) : undefined,
            };
        });

        if (this.env?.debug) {
            try {
                console.log("[P2P Dashboard] Rendering chart:", {
                    type: chartType,
                    labelsCount: labels?.length,
                    datasetsCount: datasets?.length,
                    width: canvasEl?.width,
                    height: canvasEl?.height,
                    sampleLabels: (labels || []).slice(0, 5),
                    sampleData0: (datasets?.[0]?.data || []).slice(0, 5),
                });
            } catch (_) {}
        }

        const theme = (cfg.theme === 'dark') ? 'dark' : 'light';
        const gridColor = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';
        const tickColor = theme === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)';
        const legendPosition = cfg.legendPosition || 'top';
        const isBar = chartType === 'bar';
        const isLine = chartType === 'line';
        const isRadar = chartType === 'radar';
        const isDoughnut = chartType === 'doughnut';
        const isPolar = chartType === 'polarArea';

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: Number(cfg.animationDuration) || 300 },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                decimation: isLine ? { enabled: true, algorithm: 'lttb' } : undefined,
                title: (cfg.title || this.state.title) ? { display: true, text: cfg.title || this.state.title } : { display: false },
                legend: { display: true },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const label = context.dataset?.label ? `${context.dataset.label}: ` : '';
                            const value = context.parsed?.y ?? context.parsed ?? context.raw;
                            return label + this.formatValue(value, context.dataset?.label);
                        },
                    },
                },
            },
            scales: (isDoughnut || chartType === 'pie' || isPolar || isRadar) ? undefined : {
                y: {
                    stacked: cfg.stacked === true,
                    ticks: {
                        color: tickColor,
                        callback: (val) => this._formatNumber(val),
                    },
                    grid: { color: gridColor },
                    beginAtZero: true,
                },
                x: {
                    stacked: cfg.stacked === true,
                    ticks: { color: tickColor },
                    grid: { color: gridColor },
                },
            },
        };

        if (isDoughnut) {
            options.cutout = cfg.cutout || '60%';
        }
        if (isRadar) {
            options.scales = {
                r: {
                    beginAtZero: true,
                    angleLines: { color: gridColor },
                    grid: { color: gridColor },
                    pointLabels: { color: tickColor },
                    ticks: { color: tickColor }
                }
            };
        }
        options.plugins.legend = { position: legendPosition };

        try {
            if (this._chart && this._chart.config?.type === chartType) {
                // Update existing chart
                this._chart.data.labels = labels;
                this._chart.data.datasets = datasets;
                this._chart.options = options;
                this._chart.update();
            } else {
                // Recreate chart if type changed or not existing
                if (this._chart) {
                    try { this._chart.destroy(); } catch (_) {}
                    this._chart = null;
                }
                this._chart = new Chart(ctx, { type: chartType, data: { labels, datasets }, options });
                // After creation, ensure a proper resize in case the canvas size changed
                try { this._chart.resize(); } catch (_) {}
                // Expose chart instance globally for quick inspection in debug only
                if (this.env?.debug) {
                    try {
                        window.__p2pCharts = window.__p2pCharts || [];
                        window.__p2pCharts.push({ name: this.props.name, chart: this._chart });
                        console.log("[P2P Dashboard] Chart instance stored in window.__p2pCharts");
                    } catch (_) {}
                }
            }
        } catch (e) {
            console.error('[P2P Dashboard] Failed to render chart:', e);
            this.state.hasError = true;
            this.state.errorMessage = 'Lỗi khởi tạo biểu đồ';
        }
    }

    _getDatasetColors(n, offset = 0) {
        const palette = [
            ["#4e79a7", "#2f557f"],
            ["#f28e2b", "#b96a1f"],
            ["#e15759", "#a1393b"],
            ["#76b7b2", "#4f807c"],
            ["#59a14f", "#3f6f38"],
            ["#edc948", "#b59a35"],
            ["#b07aa1", "#7b5472"],
            ["#ff9da7", "#b26c74"],
            ["#9c755f", "#6e5243"],
            ["#bab0ac", "#83807d"],
        ];
        const bg = [];
        const border = [];
        for (let i = 0; i < n; i++) {
            const idx = (i + offset) % palette.length;
            bg.push(palette[idx][0]);
            border.push(palette[idx][1]);
        }
        return { background: bg, border };
    }

    _resolveChartLib() {
        try {
            // Prefer global Chart if present (e.g., included by other modules)
            if (typeof window !== 'undefined' && window.Chart) {
                // Register default elements if available (needed for v3+ when not pre-registered)
                try {
                    if (window.Chart.register && window.Chart.registerables) {
                        window.Chart.register(...window.Chart.registerables);
                    }
                } catch (_) { /* ignore */ }
                return window.Chart;
            }
        } catch (_) {}
        return null;
    }

    _getFieldRaw() {
        if (!this.props.record || !this.props.name) return null;
        return this.props.record.data[this.props.name];
    }

    _computeSignature() {
        // signature based on raw value (string/object) and resolved chart type
        let raw = this._getFieldRaw();
        // If object, avoid cycles; raw strings are already stable
        try {
            raw = typeof raw === 'object' ? JSON.stringify(raw) : String(raw);
        } catch (_) {
            raw = String(raw);
        }
        const t = this._getChartType();
        return `${t}::${raw ?? 'null'}`;
    }
    
    /**
     * Lấy dữ liệu biểu đồ từ field value
     */
    _getChartData() {
        if (!this.props.record || !this.props.name) {
            return null;
        }
        
        const fieldValue = this.props.record.data[this.props.name];
        if (!fieldValue) {
            return null;
        }
        
        try {
            // Xử lý các trường hợp dữ liệu khác nhau
            if (typeof fieldValue === 'string') {
                return JSON.parse(fieldValue);
            } else if (typeof fieldValue === 'object') {
                return fieldValue;
            } else {
                console.warn("[P2P Dashboard] Unexpected field value type:", typeof fieldValue);
                return null;
            }
        } catch (error) {
            console.error("[P2P Dashboard] Error parsing chart data:", error);
            return null;
        }
    }

    /**
     * Lấy loại biểu đồ từ props hoặc options
     */
    _getChartType() {
        // Xác định loại biểu đồ từ nhiều nguồn (ưu tiên options)
        const allowed = new Set(["bar", "line", "pie", "doughnut", "polarArea", "radar"]);
        const normalize = (t) => {
            if (!t || typeof t !== 'string') return null;
            const lc = t.trim().toLowerCase();
            if (lc === 'donut') return 'doughnut';
            if (lc === 'polararea') return 'polarArea';
            if (["bar", "line", "pie", "doughnut", "radar"].includes(lc)) return lc;
            return null;
        };

        // 1) merged options from all sources
        const merged = this._getWidgetOptions();
        if (merged && merged.type) {
            const t = normalize(merged.type);
            if (t && allowed.has(t)) {
                if (this.env?.debug) console.log("[P2P Dashboard] Chart type from merged options:", t);
                return t;
            }
        }

        // 2) fallback to raw attrs/options paths
        const a = this.props.attrs || {};
        if (a.options) {
            if (typeof a.options === 'object' && a.options.type) {
                const t = normalize(a.options.type);
                if (t && allowed.has(t)) {
                    if (this.env?.debug) console.log("[P2P Dashboard] Chart type from attrs.options:", t);
                    return t;
                }
            }
            if (typeof a.options === 'string') {
                try {
                    const parsed = this._parseOptionsString(a.options);
                    if (parsed && parsed.type) {
                        const t = normalize(parsed.type);
                        if (t && allowed.has(t)) {
                            if (this.env?.debug) console.log("[P2P Dashboard] Chart type from attrs.options (string):", t);
                            return t;
                        }
                    }
                } catch (_) { /* ignore */ }
            }
        }

        // 3) props.type (chỉ dùng nếu hợp lệ)
        if (this.props.type) {
            const t = normalize(this.props.type);
            if (t && allowed.has(t)) {
                if (this.env?.debug) console.log("[P2P Dashboard] Chart type from props.type:", t);
                return t;
            }
        }
        // 4) attrs.type
        if (a.type) {
            const t = normalize(a.type);
            if (t && allowed.has(t)) {
                if (this.env?.debug) console.log("[P2P Dashboard] Chart type from attrs.type:", t);
                return t;
            }
        }
        // 5) field.attrs.type (legacy)
        if (this.props.field && this.props.field.attrs && this.props.field.attrs.type) {
            const t = normalize(this.props.field.attrs.type);
            if (t && allowed.has(t)) {
                if (this.env?.debug) console.log("[P2P Dashboard] Chart type from field.attrs:", t);
                return t;
            }
        }
        
        // 6) Kiểm tra từ tên field (hỗ trợ ngược)
        const fieldName = (this.props.name || '').toLowerCase();
        if (fieldName.includes('pie')) {
            if (this.env?.debug) console.log("[P2P Dashboard] Chart type from field name (pie)");
            return 'pie';
        }
        if (fieldName.includes('line')) {
            if (this.env?.debug) console.log("[P2P Dashboard] Chart type from field name (line)");
            return 'line';
        }
        if (fieldName.includes('bar')) {
            if (this.env?.debug) console.log("[P2P Dashboard] Chart type from field name (bar)");
            return 'bar';
        }
        // Giá trị mặc định
        if (this.env?.debug) console.log("[P2P Dashboard] Using default chart type: bar");
        return 'bar';
    }

    _parseOptionsString(s) {
        // Accept JSON or Python-like dict strings with single quotes.
        // 1) Try JSON.parse directly
        try { return JSON.parse(s); } catch (_) {}
        // 2) Replace single-quotes around keys/values to double-quotes naively
        // Works for simple cases like {'type': 'pie', 'height': 320}
        try {
            const normalized = s
                .trim()
                .replace(/\s*([\{,])\s*'([^']+)'\s*:/g, '$1"$2":')   // 'key': → "key":
                .replace(/:\s*'([^']*)'\s*([,\}])/g, ':"$1"$2');     // : 'val' → : "val"
            return JSON.parse(normalized);
        } catch (_) {}
        // 3) Fallback empty
        return {};
    }

    _withAlpha(hexOrRgba, alpha) {
        if (typeof hexOrRgba !== 'string') return hexOrRgba;
        if (hexOrRgba.startsWith('rgba')) {
            return hexOrRgba.replace(/rgba\(([^,]+),([^,]+),([^,]+),[^\)]+\)/, `rgba($1,$2,$3,${alpha})`);
        }
        if (hexOrRgba.startsWith('rgb(')) {
            return hexOrRgba.replace(/rgb\(([^,]+),([^,]+),([^\)]+)\)/, `rgba($1,$2,$3,${alpha})`);
        }
        const m = hexOrRgba.replace('#','');
        const r = parseInt(m.substring(0,2),16);
        const g = parseInt(m.substring(2,4),16);
        const b = parseInt(m.substring(4,6),16);
        return `rgba(${r},${g},${b},${alpha})`;
    }
    
    /**
     * Lấy tiêu đề dựa trên tên field
     */
    _getTitle() {
        const fieldName = this.props.name || '';
        let title = '';
        
        // Set appropriate title based on field name
        if (fieldName.includes('loan_status')) {
            title = 'Trạng thái khoản vay';
        } else if (fieldName.includes('loans_by_purpose')) {
            title = 'Phân loại khoản vay theo mục đích';
        } else if (fieldName.includes('loan_trend')) {
            title = 'Xu hướng số lượng khoản vay';
        } else if (fieldName.includes('loan_amount_trend')) {
            title = 'Xu hướng giá trị khoản vay';
        } else {
            title = '';
        }
        
        return title;
    }
    
    /**
     * Format giá trị số dựa trên ngữ cảnh (tiền tệ, số, %)
     */
    formatValue(value, label = '') {
        if (value === undefined || value === null) {
            return '0';
        }
        
        // Format dựa vào nhãn
        const datasetLabel = (label || '').toLowerCase();
        if (datasetLabel.includes('giá trị') || datasetLabel.includes('tiền')) {
            return this._formatCurrency(value);
        } else {
            return this._formatNumber(value);
        }
    }
    
    /**
     * Format số với dấu phân cách hàng nghìn
     */
    _formatNumber(num) {
        if (num === undefined || num === null) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    
    /**
     * Format giá trị tiền tệ
     */
    _formatCurrency(value) {
        if (value === undefined || value === null) return '0 VNĐ';
        return this._formatNumber(Math.round(value)) + ' VNĐ';
    }
    
    /**
     * Format phần trăm
     */
    formatPercent(value) {
        if (value === undefined || value === null) return '0%';
        return value.toFixed(2) + '%';
    }
    
    /**
     * Tính tổng giá trị cho một dataset
     */
    calculateTotal(datasetIndex) {
        if (!this.state.chartData || 
            !this.state.chartData.datasets || 
            !this.state.chartData.datasets[datasetIndex]) {
            return 0;
        }
        
        const values = this.state.chartData.datasets[datasetIndex].data || [];
        return values.reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
    }
    
    /**
     * Tính phần trăm cho một item
     */
    getPercentage(itemIndex) {
        if (!this.state.chartData || 
            !this.state.chartData.datasets || 
            !this.state.chartData.datasets[0]) {
            return 0;
        }
        
        const value = this.state.chartData.datasets[0].data[itemIndex] || 0;
        const total = this.calculateTotal(0);
        
        return total > 0 ? (value / total) * 100 : 0;
    }
}

// Debug helper - đã chuyển phần đăng ký sang file dashboard_graph_widget_registry.js
console.log("[P2P Dashboard] Graph renderer component defined successfully!");
