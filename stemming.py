stem_map = None

def _refresh():
    global stem_map
    with open("stemming.md", 'r') as stem_f:
        rows = [line.split(",") for line in stem_f.read().splitlines() if len(line) and line[0] != '#']

        stem_map = {prestem: row[0] for row in rows for prestem in row[1:]}

def stem(prestem):
    return stem_map.get(prestem, prestem)

_refresh()