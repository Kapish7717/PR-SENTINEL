from unidiff import PatchSet
from ..state import ReviewState

def parse_with_unidiff(raw_diff:str):
    patch = PatchSet(raw_diff)
    files=[]

    for patched_file in patch:
        files.append({
            "filename": patched_file.path,
            "added_lines": [
                (hunk_line.target_line_no, hunk_line.value)
                for hunk in patched_file
                for hunk_line in hunk
                if hunk_line.is_added
            ],
            "removed_lines": [
                (hunk_line.source_line_no, hunk_line.value)
                for hunk in patched_file
                for hunk_line in hunk
                if hunk_line.is_removed
            ],
        })
    return files

def ingest_diff(state:ReviewState)->ReviewState:
    state['parsed_files'] = parse_with_unidiff(state['raw_diff'])
    return state
