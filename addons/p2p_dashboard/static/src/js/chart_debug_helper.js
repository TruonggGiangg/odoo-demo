/**
 * Enhanced Debug Helper for P2P Dashboard Statistics
 * 
 * This file provides comprehensive debugging utilities for Dashboard statistics in Odoo.
 * To use: Load this file and run window.DashboardDebug functions in your browser console.
 * 
 * Available functions:
 * - DashboardDebug.checkStatComponents(): Checks all stats components in the page
 * - DashboardDebug.validateStatData(data): Validates statistics data structure
 * - DashboardDebug.dumpStatData(): Dumps all stat data for inspection
 * - DashboardDebug.monitorRendering(): Monitors component rendering process
 * - DashboardDebug.runFullDiagnostics(): Runs full diagnostics on all stat components
 */

/** @odoo-module **/

import { Component } from "@odoo/owl";

(function() {
    console.log("%c[Dashboard Debug] Loading enhanced dashboard debug helper...", "color: blue; font-weight: bold");
    
    // Monitor Odoo field component rendering
    if (Component && Component.prototype) {
        const originalRender = Component.prototype.render;
        if (originalRender) {
            Component.prototype.render = function() {
                if (this.constructor && this.constructor.name === 'DashboardGraphField') {
                    console.log("[Dashboard Debug] DashboardGraphField render called:", this);
                }
                return originalRender.apply(this, arguments);
            };
        }
    }
    
    // Check for dashboard components
    function checkStatComponents() {
        const statComponents = document.querySelectorAll('.o_field_dashboard_stats');
        console.log(`%c[Dashboard Debug] Found ${statComponents.length} stats components`, "color: blue; font-weight: bold");
        
        if (statComponents.length === 0) {
            console.warn("[Dashboard Debug] No stats components found on the page!");
            
            // Check if we're on a dashboard page
            const dashboardForm = document.querySelector('.o_form_view .o_dashboard_container');
            if (dashboardForm) {
                console.log("[Dashboard Debug] Found dashboard form, but no stats components");
            } else {
                console.log("[Dashboard Debug] No dashboard form found on the page");
            }
            
            return;
        }
        
        statComponents.forEach((component, index) => {
            console.log(`%c[Dashboard Debug] Stats component ${index + 1}:`, "color: blue", component);
            
            const container = component.querySelector('.p2p-stats-container');
            if (container) {
                console.log(`  Container found:`, container);
                
                const table = container.querySelector('table');
                if (table) {
                    console.log(`  Table found with ${table.rows.length} rows`);
                    
                    // Check table structure
                    const thead = table.querySelector('thead');
                    const tbody = table.querySelector('tbody');
                    const tfoot = table.querySelector('tfoot');
                    
                    console.log(`  Table structure: thead=${thead ? 'Yes' : 'No'}, tbody=${tbody ? 'Yes' : 'No'}, tfoot=${tfoot ? 'Yes' : 'No'}`);
                    
                    if (tbody) {
                        console.log(`  Table body has ${tbody.rows.length} rows`);
                    }
                } else {
                    console.log(`  No table found, might be empty data`);
                    
                    // Check for empty message
                    const emptyMsg = container.querySelector('.p2p-stats-empty');
                    if (emptyMsg) {
                        console.log(`  Empty message found: "${emptyMsg.textContent}"`);
                    }
                }
            } else {
                console.error(`  No container element found in component`);
            }
            
            // Check CSS properties
            const componentStyle = getComputedStyle(component);
            console.log(`  Component style:`, {
                position: componentStyle.position,
                display: componentStyle.display,
                width: componentStyle.width,
                height: componentStyle.height,
                zIndex: componentStyle.zIndex,
                overflow: componentStyle.overflow,
                visibility: componentStyle.visibility,
                opacity: componentStyle.opacity
            });
        });
        
        return statComponents;
    }
    
    // Check if an element is visible
    function isElementVisible(element) {
        if (!element) return false;
        
        const style = getComputedStyle(element);
        
        if (style.display === 'none') return false;
        if (style.visibility !== 'visible') return false;
        if (style.opacity === '0') return false;
        
        const rect = element.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;
        
        // Check if element is in the viewport
        const isInViewport = (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
        
        return isInViewport;
    }
    
    // Validate statistics data structure
    function validateStatData(data) {
        console.log(`[Dashboard Debug] Validating stat data:`, data);
        
        if (!data) {
            console.error(`[Dashboard Debug] Stat data is null or undefined`);
            return false;
        }
        
        if (typeof data !== 'object') {
            console.error(`[Dashboard Debug] Stat data is not an object, got ${typeof data}`);
            return false;
        }
        
        // Check labels
        if (!Array.isArray(data.labels)) {
            console.error(`[Dashboard Debug] Stat labels is not an array, got ${typeof data.labels}`);
            return false;
        }
        
        // Check datasets
        if (!Array.isArray(data.datasets)) {
            console.error(`[Dashboard Debug] Stat datasets is not an array, got ${typeof data.datasets}`);
            return false;
        }
        
        // Check each dataset
        let isValid = true;
        data.datasets.forEach((dataset, index) => {
            console.log(`[Dashboard Debug] Checking dataset ${index + 1}:`, dataset);
            
            if (!dataset.label) {
                console.warn(`[Dashboard Debug] Dataset ${index + 1} missing label`);
            }
            
            if (!Array.isArray(dataset.data)) {
                console.error(`[Dashboard Debug] Dataset ${index + 1} data is not an array, got ${typeof dataset.data}`);
                isValid = false;
            } else if (dataset.data.length === 0) {
                console.warn(`[Dashboard Debug] Dataset ${index + 1} has empty data array`);
            }
        });
        
        return isValid;
    }
    
    // Dump all statistics data
    function dumpStatData() {
        // Find all fields with p2p_dashboard_graph widget
        const statFields = document.querySelectorAll('[widget="p2p_dashboard_graph"]');
        console.log(`[Dashboard Debug] Found ${statFields.length} stat fields`);
        
        // For each field, try to find the component and extract data
        const componentsData = [];
        statFields.forEach((field, index) => {
            const fieldName = field.getAttribute('name');
            console.log(`[Dashboard Debug] Examining field ${index + 1}: ${fieldName}`);
            
            // Find the component for this field
            const component = document.querySelector(`.o_field_widget[name="${fieldName}"]`);
            if (component) {
                console.log(`[Dashboard Debug] Found component for field ${fieldName}`);
                
                // Try to extract data from component's state
                const table = component.querySelector('table');
                if (table) {
                    const rowCount = table.querySelector('tbody')?.rows.length || 0;
                    const headerCells = table.querySelector('thead tr')?.cells.length || 0;
                    
                    componentsData.push({
                        fieldName,
                        hasTable: true,
                        rowCount,
                        headerCells
                    });
                } else {
                    componentsData.push({
                        fieldName,
                        hasTable: false,
                        isEmpty: !!component.querySelector('.p2p-stats-empty')
                    });
                }
            } else {
                console.warn(`[Dashboard Debug] No component found for field ${fieldName}`);
            }
        });
        
        console.log(`[Dashboard Debug] All components data:`, componentsData);
        return componentsData;
    }
    
    // Monitor component rendering process
    function monitorRendering() {
        console.log(`[Dashboard Debug] Starting component rendering monitor`);
        
        // Find all field components that might render dashboard stats
        const components = odoo.__DEBUG__?.services?.component?.componentRegistry || [];
        const dashboardComponents = Array.from(components).filter(c => 
            c && c.name && (c.name.includes('Dashboard') || c.name.includes('Graph') || c.name.includes('Stat'))
        );
        
        console.log(`[Dashboard Debug] Found ${dashboardComponents.length} potential dashboard components:`, dashboardComponents);
        
        // Monitor for new components
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    Array.from(mutation.addedNodes).forEach((node) => {
                        if (node.classList && node.classList.contains('o_field_dashboard_stats')) {
                            console.log(`[Dashboard Debug] New dashboard stats component detected:`, node);
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log(`[Dashboard Debug] Mutation observer started`);
        
        // Return a function to stop monitoring
        return function stopMonitoring() {
            observer.disconnect();
            console.log(`[Dashboard Debug] Component rendering monitor stopped`);
        };
    }
    
    // Run full diagnostics
    function runFullDiagnostics() {
        console.log(`%c[Dashboard Debug] Running full diagnostics...`, "color: blue; font-weight: bold");
        
        // 1. Check stats components
        const components = checkStatComponents();
        
        // 2. Dump stats data
        const statsData = dumpStatData();
        
        // 3. Check for errors in the console
        console.log(`[Dashboard Debug] Check console for any dashboard-related errors`);
        
        // 4. Check if styles are loaded properly
        const styles = document.querySelectorAll('link[rel="stylesheet"]');
        const dashboardStyles = Array.from(styles).filter(s => 
            s.href && (s.href.includes('dashboard') || s.href.includes('stats'))
        );
        
        console.log(`[Dashboard Debug] Found ${dashboardStyles.length} dashboard-related stylesheets:`, dashboardStyles);
        
        // 5. Check viewport and responsive settings
        console.log(`[Dashboard Debug] Viewport size: ${window.innerWidth}x${window.innerHeight}`);
        
        // 6. Summary
        console.log(`%c[Dashboard Debug] Diagnostics summary:`, "color: blue; font-weight: bold");
        console.log(`- Dashboard components: ${components ? components.length : 0}`);
        console.log(`- Stats fields: ${statsData.length}`);
        console.log(`- Fields with tables: ${statsData.filter(d => d.hasTable).length}`);
        console.log(`- Empty fields: ${statsData.filter(d => !d.hasTable && d.isEmpty).length}`);
        
        // Return diagnostic results
        return {
            components: components ? components.length : 0,
            statsFields: statsData.length,
            fieldsWithTables: statsData.filter(d => d.hasTable).length,
            emptyFields: statsData.filter(d => !d.hasTable && d.isEmpty).length,
            viewportSize: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        };
    }
    
    // Export debug functions to global scope
    window.DashboardDebug = {
        checkStatComponents,
        isElementVisible,
        validateStatData,
        dumpStatData,
        monitorRendering,
        runFullDiagnostics
    };
    
    console.log("%c[Dashboard Debug] Enhanced dashboard debug helper loaded. Use DashboardDebug.runFullDiagnostics() to run full diagnostics.", "color: green; font-weight: bold");
})();