{% for fdw_user in fdw_users %}
    -- You can't remove a user if they have permissions on anything, so we need
    -- to scrub the permissions before we can start. However you can't remove
    -- permissions from a user that doesn't exist, so we end up with a
    -- Catch-22, forcing us to check and conditionally execute the following.
    DO
    $$BEGIN
        IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{{ fdw_user }}') THEN
            EXECUTE 'REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM "{{ fdw_user }}"';
            EXECUTE 'REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA report FROM "{{ fdw_user }}"';
            EXECUTE 'REVOKE USAGE ON SCHEMA public FROM "{{ fdw_user }}"';
            EXECUTE 'REVOKE USAGE ON SCHEMA report FROM "{{ fdw_user }}"';
            EXECUTE 'DROP USER IF EXISTS "{{ fdw_user }}"';
        END IF;
    END$$;

    CREATE USER "{{ fdw_user }}";
    ALTER USER "{{ fdw_user }}" PASSWORD 'password';  -- No need to hide this
{% endfor %}
