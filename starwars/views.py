import json
import sqlparse

from django.http import HttpResponse
from django.shortcuts import render
from django.db import connection


def live_sql_editor(request):
    if request.method == "POST":
        # read the query from request
        user_query = json.loads(request.POST.get("query"))
        columns = []
        queryset = None
        error_message = None  # handling error messages
        if user_query:
            # open a connection to the DB
            with connection.cursor() as cursor:
                try:
                    # only allow SELECT queries to be run. it will also allow (with CTEs)
                    parsed_statement = sqlparse.parse(user_query)
                    for statement in parsed_statement:
                        if statement.get_type() != "SELECT":
                            raise Exception("Invalid query! Only select statements are allowed")
                    # execute SQL with cursor
                    cursor.execute(user_query)
                    columns = [col[0] for col in cursor.description]
                    queryset = cursor.fetchall()
                except Exception as e:
                    error_message = str(e)
        context = {
            "columns": columns,
            "rows": queryset,
            "error": error_message
        }
        return HttpResponse(json.dumps(context), content_type="application/json")
    context = {
        "endpoint": "/admin/live-editor/"
    }
    return render(request, "admin/live_editor.html", context)
