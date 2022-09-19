homonym_map = None

def _refresh():
    global homonym_map
    with open("homonyms.md", 'r') as homonym_f:
        rows = [line.split(",") for line in homonym_f.read().splitlines() if len(line) and line[0] != '#']
        homonym_map = {homonym: row[0] for row in rows for homonym in row[1:]}



def homonym(raw_homonym):
    return homonym_map.get(raw_homonym, raw_homonym)

_refresh()