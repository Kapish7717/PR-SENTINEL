import subprocess
import json


def get_added_lines_text(parsed_files: list, filename: str) -> str:
    for f in parsed_files:
        if f["filename"] == filename:
            return "\n".join(content for _, content in f["added_lines"])
    return "" 

def verify_findings(findings,parsed_files):
    verified = []
    for finding in findings:
        file_lines = get_added_lines_text(parsed_files, finding["file"])
        if finding["evidence"] in file_lines:   # proof real diff mein hai?
            verified.append(finding)
        else:
            print(f"Removed fake findings: {finding}")
    return verified



