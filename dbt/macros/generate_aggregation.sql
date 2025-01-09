{% macro generate_aggregation(table_name) %}
    {% set user_schemas = get_user_schemas() %}

    {% for schema in user_schemas %}
        select 
            *
        from {{ schema }}.{{ table_name }}
        {% if not loop.last %}
            union all
        {% endif %}
    {% endfor %}
{% endmacro %}