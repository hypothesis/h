-- The public schema already exists but
-- we need to grant usage to the user will map via fdw.
{% for fdw_user in fdw_users %}
GRANT USAGE ON SCHEMA public TO "{{fdw_user}}";
GRANT SELECT ON  public.user_group TO "{{fdw_user}}";
GRANT SELECT ON  public."user" TO "{{fdw_user}}";
GRANT SELECT ON  public."group" TO "{{fdw_user}}";
{% endfor %}

{% for fdw_user in fdw_users %}
GRANT USAGE ON SCHEMA report TO "{{fdw_user}}";
GRANT SELECT ON ALL TABLES IN SCHEMA report TO "{{fdw_user}}";
{% endfor %}


-- Empty query in case fdw_users is empty.
select null;
