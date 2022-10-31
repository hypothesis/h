{% for fdw_user in fdw_users %}
GRANT USAGE ON SCHEMA report TO "{{fdw_user}}";
GRANT SELECT ON ALL TABLES IN SCHEMA report TO "{{fdw_user}}";
{% endfor %}
