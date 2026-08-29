{#
    Override standard documenté par dbt Labs (https://docs.getdbt.com/docs/build/custom-schemas) :
    par défaut dbt concatène target.schema + custom_schema_name (ex. "public_marts"). Ici, un
    custom_schema_name explicite (+schema: marts) remplace entièrement le schéma cible au lieu
    de s'y concaténer, pour obtenir skillwatch_warehouse.marts.* plutôt que public_marts.*.
#}

{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}

        {{ default_schema }}

    {%- else -%}

        {{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}
