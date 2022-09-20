synonym_map:dict[str,str] = None
stem_map:dict[str,str] = None
style_map:dict[str,str] = None

root_synonyms:set[str] = None
non_root_synonyms:set[str] = None



# stem_map:     Put in a lowercase term,         get the titlecase term it stems to
# synonym_map:  Put in a lowercase stemmed term, get the lowercase stemmed skill it's a synonym for
# style_map:    Put in a lowercase stemmed term, get the titlecase stemmed term  it's shown as

# root_synonyms:     A set of lowercase stemmed skills which are       the 'root' of their synonym group
# non_root_synonyms: A set of lowercase stemmed skills which are *not* the 'root' of their synonym group


def _refresh():
    global synonym_map
    global root_synonyms
    global non_root_synonyms
    global stem_map
    global style_map

    with open("stemming.md", 'r') as stem_f:
        rows = [line.split(",") for line in stem_f.read().splitlines() if len(line) and line[0] != '#']  
        stem_map = {
            prestem.lower():row[0] # From lowercase text to stemmed (titlecase) text
            for row in rows
            for prestem in row}

    with open("synonyms.md", 'r') as synonym_f:
        stemmed_rows = [
            [stem(prestem) for prestem in line.split(",")]
            for line in synonym_f.read().splitlines() if len(line) and line[0] != '#']

        synonym_map = {
            stemmed_synonym.lower(): stemmed_row[0].lower() # From synonyms to roots of synonyms
            for stemmed_row in stemmed_rows 
            for stemmed_synonym in stemmed_row}
            
        root_synonyms =      {stemmed_row[0].lower() for stemmed_row in stemmed_rows}
        non_root_synonyms = {stemmed_synonym.lower() for stemmed_row in stemmed_rows for stemmed_synonym in stemmed_row[1:]}

        style_map = {stemmed_term.lower():stemmed_term # From terms.lower to the original term
                    for stemmed_row in stemmed_rows 
                    for stemmed_term in stemmed_row}


def stem(prestem:str) -> str:
    return stem_map.get(prestem.lower(), prestem)

def synonym(raw_synonym:str) -> str:
    stemmed_synonym = stem(raw_synonym).lower()
    return synonym_map.get(stemmed_synonym, stemmed_synonym)

def stylize(raw_skill_term:str) -> str:
    stemmed_skill_term = stem(raw_skill_term)
    return style_map.get(stemmed_skill_term.lower(), stemmed_skill_term)

_refresh()