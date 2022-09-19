synonym_map = None
root_synonyms = None
non_root_synonyms = None

def _refresh():
    global synonym_map
    global root_synonyms
    global non_root_synonyms
    with open("synonyms.md", 'r') as synonym_f:
        rows = [line.split(",") for line in synonym_f.read().splitlines() if len(line) and line[0] != '#']
        synonym_map = {synonym: row[0] for row in rows for synonym in row}
        root_synonyms = {row[0] for row in rows}
        non_root_synonyms = {synonym for row in rows for synonym in row[1:]}




def synonym(raw_synonym):
    return synonym_map.get(raw_synonym, raw_synonym)

_refresh()