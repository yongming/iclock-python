[
{% for item in latest_item_list %}
{"DeptID":"{{ item.DeptID }}","DeptName":"{{ item.DeptName }}","parent":"{{ item.parent }}"}{%if not forloop.last%},{%endif%}
{% endfor %}
]