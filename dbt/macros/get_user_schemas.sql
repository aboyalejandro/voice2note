{% macro get_user_schemas() %}
    {% set query %}
        select distinct concat('user_', user_id) as schema_name
        from {{ ref('stg_users') }}
    {% endset %}
    
    {% set results = run_query(query) %}
    {% set schemas = [] %}
    
    {% if execute %}
        {% for row in results.rows %}
            {% do schemas.append(row.schema_name) %}
        {% endfor %}
    {% endif %}
    
    {{ return(schemas) }}
{% endmacro %}