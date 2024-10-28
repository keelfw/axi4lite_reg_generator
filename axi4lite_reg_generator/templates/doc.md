# {{ entity_name }} Register Definitions

Data Size = {{ data_size }} bits

# Address Map
| Address | Name | Type |
| ------- | ---- | ---- |
{% for reg in regs -%}
| {{ reg['addr_offset'] }} | [{{ reg['name'] }}](#{{ reg['name']|lower }}) | {{ reg['reg_type'] }} |
{% endfor -%}

# Register Definitions

{% for reg in regs %}
## {{ reg['name'] }}
{{ reg['description'] }}

* **Address**: {{ reg['addr_offset'] }}
* **Register Type**: {{ reg['reg_type'] }}
* **Update Pulse**: {{ reg['use_upd_pulse'] }}

| high | low | Name {% if reg['reg_type'] != 'ro' %} | Default {% endif %}| Description |
| ---- | --- | ---- {% if reg['reg_type'] != 'ro' %} | ------- {% endif %}| ----------- |
{% if reg['bits']|count_bits != data_size -%}
| {{ data_size-1 }} | {{ reg['bits']|count_bits }} | Unused {% if reg['reg_type'] != 'ro' %} | 0 {% endif %}| Unused Bits |
{% endif -%}
{% if reg['bits'] is integer -%}
| {{ reg['bits']|count_bits-1 }} | 0 | {{ reg['name'] }} {% if reg['reg_type'] != 'ro' %} | 0 {% endif -%}||
{% elif reg['bits'] is mapping -%}
| {{ reg['bits']|count_bits-1 }} | 0 | {{ reg['name'] }} {% if reg['reg_type'] != 'ro' %} | {{ reg['bits']['default_value'] }} {% endif -%}||
{% else -%}
  {% for bit_field in reg['bits'] -%}
    | {{ reg['bits']|get_offset(bit_field['field_name']) + bit_field['num_bits'] - 1 }} | {{ reg['bits']|get_offset(bit_field['field_name']) }} | {{ bit_field['field_name'] }} {% if reg['reg_type'] != 'ro' %} | {{ bit_field['default_value'] }} {% endif -%}| {{ bit_field['description'] }} |
  {% endfor -%}
{% endif %}
{% endfor %}