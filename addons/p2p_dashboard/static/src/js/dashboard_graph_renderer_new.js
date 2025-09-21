/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useRef, onMounted, onWillUpdateProps, onWillDestroy, onWillStart, onPatched } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

/**
 * Text-based Dashboard Graph Field for P2P Dashboard
 * 
 * This widget renders statistics as text instead of charts
 */
export class DashboardGraphField extends Component {
    static template = 'p2p_dashboard.GraphRenderer';
    
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.containerRef = useRef("container");
        
        onMounted(() => {
            this._renderStats();
        });
        
        onPatched(() => {
            this._renderStats();
        });
    }
    
    /**
     * Get field value based on field name from record
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
            if (typeof fieldValue === 'string') {
                return JSON.parse(fieldValue);
            }
            return fieldValue;
        } catch (error) {
            console.error("[P2P Dashboard] Error parsing chart data:", error);
            return null;
        }
    }

    /**
     * Get chart type from props or field options
     */
    _getChartType() {
        // First try to get from props.type directly
        if (this.props.type) {
            return this.props.type;
        }
        
        // Then try to get from options if available
        if (this.props.options && this.props.options.type) {
            return this.props.options.type;
        }
        
        // Try to get from field attrs
        if (this.props.field && this.props.field.attrs && this.props.field.attrs.type) {
            return this.props.field.attrs.type;
        }
        
        // Finally, check if the name contains a type hint (for backward compatibility)
        const fieldName = this.props.name || '';
        if (fieldName.includes('pie')) return 'pie';
        if (fieldName.includes('line')) return 'line';
        if (fieldName.includes('bar')) return 'bar';
        
        return 'bar'; // Default chart type
    }
    
    /**
     * Format number with thousands separator
     */
    _formatNumber(num) {
        if (num === undefined || num === null) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    
    /**
     * Format monetary value
     */
    _formatCurrency(value) {
        if (value === undefined || value === null) return '0 VNĐ';
        return this._formatNumber(Math.round(value)) + ' VNĐ';
    }
    
    /**
     * Format percentage
     */
    _formatPercent(value) {
        if (value === undefined || value === null) return '0%';
        return value.toFixed(2) + '%';
    }
    
    /**
     * Render the statistics as text
     */
    _renderStats() {
        if (!this.containerRef || !this.containerRef.el) {
            return;
        }
        
        // Get chart data
        const chartData = this._getChartData();
        if (!chartData) {
            this._renderEmptyStats();
            return;
        }
        
        // Get chart type
        const chartType = this._getChartType();
        
        // Clear previous content
        this.containerRef.el.innerHTML = '';
        
        // Create stats container
        const statsContainer = document.createElement('div');
        statsContainer.className = 'p2p-stats-container';
        
        try {
            const labels = chartData.labels || [];
            const datasets = chartData.datasets || [];
            
            if (chartType === 'pie' || chartType === 'bar') {
                // Create a table for the statistics
                const table = document.createElement('table');
                table.className = 'table table-bordered table-hover p2p-stats-table';
                
                // Create table header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                const headerLabel = document.createElement('th');
                headerLabel.textContent = 'Danh mục';
                headerRow.appendChild(headerLabel);
                
                for (const dataset of datasets) {
                    const headerValue = document.createElement('th');
                    headerValue.textContent = dataset.label || 'Giá trị';
                    headerRow.appendChild(headerValue);
                }
                
                const headerPercent = document.createElement('th');
                headerPercent.textContent = 'Phần trăm';
                headerRow.appendChild(headerPercent);
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create table body
                const tbody = document.createElement('tbody');
                
                // Calculate total for percentage
                let totals = datasets.map(dataset => {
                    return dataset.data.reduce((sum, value) => sum + (parseFloat(value) || 0), 0);
                });
                
                // Add rows for each label
                for (let i = 0; i < labels.length; i++) {
                    const row = document.createElement('tr');
                    
                    const labelCell = document.createElement('td');
                    labelCell.textContent = labels[i];
                    row.appendChild(labelCell);
                    
                    for (let j = 0; j < datasets.length; j++) {
                        const valueCell = document.createElement('td');
                        const value = datasets[j].data[i] || 0;
                        
                        // Determine if this is likely a monetary value based on dataset label
                        const datasetLabel = (datasets[j].label || '').toLowerCase();
                        if (datasetLabel.includes('giá trị') || datasetLabel.includes('tiền')) {
                            valueCell.textContent = this._formatCurrency(value);
                        } else {
                            valueCell.textContent = this._formatNumber(value);
                        }
                        
                        row.appendChild(valueCell);
                        
                        // Only add percentage for the first dataset to avoid confusion
                        if (j === 0) {
                            const percentCell = document.createElement('td');
                            const percent = totals[j] > 0 ? (value / totals[j]) * 100 : 0;
                            percentCell.textContent = this._formatPercent(percent);
                            row.appendChild(percentCell);
                        }
                    }
                    
                    tbody.appendChild(row);
                }
                
                // Add a total row
                const totalRow = document.createElement('tr');
                totalRow.className = 'p2p-stats-total';
                
                const totalLabelCell = document.createElement('td');
                totalLabelCell.textContent = 'Tổng cộng';
                totalLabelCell.style.fontWeight = 'bold';
                totalRow.appendChild(totalLabelCell);
                
                for (let j = 0; j < datasets.length; j++) {
                    const totalValueCell = document.createElement('td');
                    totalValueCell.style.fontWeight = 'bold';
                    
                    const datasetLabel = (datasets[j].label || '').toLowerCase();
                    if (datasetLabel.includes('giá trị') || datasetLabel.includes('tiền')) {
                        totalValueCell.textContent = this._formatCurrency(totals[j]);
                    } else {
                        totalValueCell.textContent = this._formatNumber(totals[j]);
                    }
                    
                    totalRow.appendChild(totalValueCell);
                    
                    if (j === 0) {
                        const totalPercentCell = document.createElement('td');
                        totalPercentCell.textContent = '100%';
                        totalPercentCell.style.fontWeight = 'bold';
                        totalRow.appendChild(totalPercentCell);
                    }
                }
                
                tbody.appendChild(totalRow);
                table.appendChild(tbody);
                statsContainer.appendChild(table);
                
            } else if (chartType === 'line') {
                // For trend data, create a table
                const table = document.createElement('table');
                table.className = 'table table-bordered table-hover p2p-stats-table';
                
                // Create table header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                const headerPeriod = document.createElement('th');
                headerPeriod.textContent = 'Kỳ';
                headerRow.appendChild(headerPeriod);
                
                for (const dataset of datasets) {
                    const headerValue = document.createElement('th');
                    headerValue.textContent = dataset.label || 'Giá trị';
                    headerRow.appendChild(headerValue);
                }
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create table body
                const tbody = document.createElement('tbody');
                
                // Add rows for each period
                for (let i = 0; i < labels.length; i++) {
                    const row = document.createElement('tr');
                    
                    const periodCell = document.createElement('td');
                    periodCell.textContent = labels[i];
                    row.appendChild(periodCell);
                    
                    for (let j = 0; j < datasets.length; j++) {
                        const valueCell = document.createElement('td');
                        const value = datasets[j].data[i] || 0;
                        
                        // Determine if this is likely a monetary value based on dataset label
                        const datasetLabel = (datasets[j].label || '').toLowerCase();
                        if (datasetLabel.includes('giá trị') || datasetLabel.includes('tiền')) {
                            valueCell.textContent = this._formatCurrency(value);
                        } else {
                            valueCell.textContent = this._formatNumber(value);
                        }
                        
                        row.appendChild(valueCell);
                    }
                    
                    tbody.appendChild(row);
                }
                
                table.appendChild(tbody);
                statsContainer.appendChild(table);
            }
            
            this.containerRef.el.appendChild(statsContainer);
            
        } catch (error) {
            console.error("[P2P Dashboard] Error rendering stats:", error);
            this._renderEmptyStats("Lỗi hiển thị thống kê: " + error.message);
        }
    }
    
    /**
     * Render an empty stats message
     */
    _renderEmptyStats(message = "Không có dữ liệu thống kê") {
        if (!this.containerRef || !this.containerRef.el) {
            return;
        }
        
        // Clear content
        this.containerRef.el.innerHTML = '';
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = 'p2p-stats-empty';
        messageElement.textContent = message;
        
        this.containerRef.el.appendChild(messageElement);
    }
}

// Register the field component
registry.category("fields").add("p2p_dashboard_graph", DashboardGraphField);

// Register the template
registry.category("templates").add("p2p_dashboard.GraphRenderer", `
    <div class="o_field_dashboard_stats">
        <div t-ref="container" class="p2p-stats-container"></div>
    </div>
`);