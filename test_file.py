import os
import json  # Unused import (will trigger the ruff linter)

def get_user_data(username):
    # SQL Injection vulnerability (will trigger the LLM agent)
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return db.execute(query)
