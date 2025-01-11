-- Create role for user schema management
CREATE ROLE role_user_schema;

-- Create application users
CREATE USER app WITH PASSWORD '...';
CREATE USER aws_lambda WITH PASSWORD '...';
CREATE USER airbyte WITH PASSWORD '...';
CREATE USER dbt_analytics WITH PASSWORD '...';

-- Database level permissions
GRANT CONNECT ON DATABASE voice2note TO app;
GRANT CREATE ON DATABASE voice2note TO app;
GRANT CONNECT ON DATABASE voice2note TO aws_lambda;
GRANT CONNECT ON DATABASE voice2note TO dbt_analytics;

-- Public schema permissions for app user
GRANT USAGE, CREATE ON SCHEMA public TO app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO app;

-- Role management for app
ALTER ROLE app WITH CREATEROLE;
GRANT role_user_schema TO app WITH ADMIN OPTION;

-- Grant app role to postgres for administration
GRANT app TO postgres WITH ADMIN OPTION;

-- Set up role_user_schema default privileges
ALTER DEFAULT PRIVILEGES FOR ROLE role_user_schema IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO role_user_schema;
ALTER DEFAULT PRIVILEGES FOR ROLE role_user_schema IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO role_user_schema;

-- Setup CDC with Airbyte 
ALTER USER airbyte REPLICATION;
SELECT pg_create_logical_replication_slot('airbyte_slot', 'pgoutput');
CREATE PUBLICATION airbyte_publication FOR ALL TABLES;
GRANT USAGE ON SCHEMA analytics TO airbyte;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO airbyte;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO airbyte;

-- Setup dbt_analytics user
GRANT CONNECT ON DATABASE voice2note TO dbt_analytics;
GRANT USAGE ON SCHEMA public TO dbt_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dbt_analytics;
