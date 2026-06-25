import os  # Unused import (Ruff should catch this)

def divide_by_zero():
    return 1 / 0  # Logic bug (Groq should catch this)

def sql_injection():
    user_input = request.args.get("username")
    query = "SELECT * FROM users WHERE username = '" + user_input + "'"
    cursor.execute(query)  # SQL Injection vulnerability