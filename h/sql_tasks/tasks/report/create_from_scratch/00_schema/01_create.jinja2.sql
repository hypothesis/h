DROP SCHEMA IF EXISTS report CASCADE;
CREATE SCHEMA report AUTHORIZATION "{{db_user}}";

{% for fdw_user in fdw_users %}
GRANT USAGE ON SCHEMA report TO "{{fdw_user}}";
{% endfor %}
