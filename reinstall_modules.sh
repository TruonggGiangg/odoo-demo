#!/bin/bash
# Script to reinstall modules in correct order

# Update the module list
echo "Updating module list..."
python3 /mnt/extra-addons/odoo/odoo-bin -c /etc/odoo/odoo.conf --stop-after-init -u base

# Make sure p2p_bridge is installed first
echo "Installing p2p_bridge..."
python3 /mnt/extra-addons/odoo/odoo-bin -c /etc/odoo/odoo.conf --stop-after-init -i p2p_bridge

# Then install website_custom_snippet
echo "Installing website_custom_snippet..."
python3 /mnt/extra-addons/odoo/odoo-bin -c /etc/odoo/odoo.conf --stop-after-init -i website_custom_snippet

echo "Done!"