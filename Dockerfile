FROM odoo:18
USER root
COPY ./addons /mnt/extra-addons
COPY ./etc/odoo.conf /etc/odoo/odoo.conf
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh

# Give execute permissions to the entrypoint script
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Give ownership of the /etc/odoo directory to the odoo user
RUN chown -R odoo:odoo /etc/odoo

# Ensure data dir exists and owned by odoo
RUN mkdir -p /var/lib/odoo && chown -R odoo:odoo /var/lib/odoo

USER odoo
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]