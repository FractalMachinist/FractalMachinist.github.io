stem_map = None

def _refresh():
    global stem_map
    with open("stemming.txt", 'r') as stem_f:
        stem_map = {prestem: row[0] for row in map(lambda r: r.replace("\n", "").split(","), stem_f.readlines()) for prestem in row[1:]}

def stem(prestem):
    return stem_map.get(prestem, prestem)

_refresh()