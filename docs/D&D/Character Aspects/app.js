// Minimal Aspect Builder app.js
// Split browser storage into three keys so parts can be saved/cleared independently
const ASPECTS_KEY = 'aspect_builder_aspects_v1'; // groups / aspects
const CAST_KEY = 'aspect_builder_cast_v1';       // cast array
const UI_KEY = 'aspect_builder_ui_v1';           // UI state (activeId, etc.)

let state = {
    groups: [],
    cast: [],
    activeId: null,
    // track last random-generated character to allow quick duplicates to be removed
    // shape: { id: string, time: number }
    lastRandom: null
};

// time window (ms) within which a previous random character will be removed
const RANDOM_DEBOUNCE_MS = 5000;

// Maximum allowed suggested name length (characters). If a chosen suffix would
// make the name exceed this length, try other suffixes or omit the suffix.
const NAME_MAX_LENGTH = 28;

// Helpers
function genId(prefix = 'id') { return prefix + Math.random().toString(36).slice(2, 9) }
// Roman numeral helpers for "royal" name incrementing
function romanToInt(s) {
    if (!s) return 0;
    s = s.toUpperCase();
    const map = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
    let total = 0;
    for (let i = 0; i < s.length; i++) {
        const val = map[s[i]] || 0;
        const next = map[s[i + 1]] || 0;
        if (val < next) total -= val; else total += val;
    }
    return total;
}

function intToRoman(num) {
    if (!num || num <= 0) return '';
    const vals = [[1000, 'M'], [900, 'CM'], [500, 'D'], [400, 'CD'], [100, 'C'], [90, 'XC'], [50, 'L'], [40, 'XL'], [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']];
    let out = '';
    for (const [v, sym] of vals) {
        while (num >= v) { out += sym; num -= v; }
    }
    return out;
}

// If name ends with a Roman numeral, increment it (Edward V -> Edward VI).
// If name has no trailing numeral, append " II" (Edward -> Edward II).
function incrementRoyalName(name) {
    if (!name) return name;
    const trimmed = name.trim();
    if (!trimmed) return name;
    // match a trailing Roman numeral token (space followed by letters made of MDCLXVI)
    const m = trimmed.match(/^(.*\S)\s+([MDCLXVI]+)\s*$/i);
    if (m) {
        const base = m[1];
        const roman = m[2];
        const val = romanToInt(roman);
        // if roman parsing failed, fall back to appending II
        if (!val) return trimmed + ' II';
        return base + ' ' + intToRoman(val + 1);
    }
    return trimmed + ' II';
}

// Given a candidate name and the current cast array, return a name using
// the next available royal numeral so that no duplicate names are produced.
// Examples: cloning "Travis" repeatedly -> "Travis II", "Travis III", ...
function makeUniqueRoyalName(name, cast) {
    if (!name) return name;
    const trimmed = name.trim();
    if (!trimmed) return name;

    // Extract base (strip trailing roman if present)
    const m = trimmed.match(/^(.*\S)\s+([MDCLXVI]+)\s*$/i);
    const base = m ? m[1] : trimmed;
    const baseNorm = base.trim().toLowerCase();

    // Build a set of existing names for fast collision checks
    const existing = new Set((cast || []).map(c => (c.name || '').trim()));

    // Find the highest numeral currently used for this base. Treat a bare
    // base-name (e.g. "Travis") as occupying "1" so the first clone becomes II.
    let max = 0;
    (cast || []).forEach(c => {
        const cn = (c.name || '').trim();
        if (!cn) return;
        const cm = cn.match(/^(.*\S)\s+([MDCLXVI]+)\s*$/i);
        if (cm) {
            const b = cm[1].trim().toLowerCase();
            if (b === baseNorm) {
                const val = romanToInt(cm[2]);
                if (val > max) max = val;
            }
        } else {
            if (cn.trim().toLowerCase() === baseNorm) {
                if (1 > max) max = 1;
            }
        }
    });

    // Start with the next numeral after the current max. Ensure at least II.
    let next = Math.max(2, max + 1);
    let candidate = base + ' ' + intToRoman(next);
    // If candidate collides with an existing literal name (somebody manually
    // created the same roman), bump until free.
    while (existing.has(candidate)) {
        next++;
        candidate = base + ' ' + intToRoman(next);
        if (next > 10000) break; // safety
    }
    return candidate;
}

// Very silly name generator -------------------------------------------------
// Produces a large-ish space of playful names like "CatBoy McCatPants" or
// "Wiiiiide Larry" by combinatorially joining small lists. Keep the output
// fresh by returning a randomly-built string; collisions are acceptable.
function randomChoice(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
// helper: small chance to elongate a vowel in a token
function elongate(s) {
    if (typeof s !== 'string' || !s) return s;
    if (Math.random() < 0.01) {
        // Only elongate vowels not preceded by 'q' (case-insensitive)
        return s.replace(/(?<!q)([aeiouy])/i, m => m + m.repeat(Math.floor(Math.random() * 4) + 2));
    }
    return s;
}
// helper: lightweight keyword extraction from aspect strings (no heavyweight NLP).
function extractKeywords(aspectsList) {
    if (!Array.isArray(aspectsList) || aspectsList.length === 0) return [];
    const stop = new Set(['of','and','the','a','an','to','in','with','for','is','my','i','it','its','on','from','by','that','this','than','when','was','are','be','as','not','but','or','at','into','over','under','who','what','which']);
    const nounSuffixes = ['ion','ment','ness','ity','er','or','ship','hood','age','ing','al','ism','ty'];
    const freq = new Map();
    // capture multi-word TitleCase phrases first (e.g., "Whispered Inheritance")
    aspectsList.forEach(s => {
        if (!s) return;
        const original = String(s).trim();
        // normalized form for whole-aspect comparisons (strip punctuation)
        const normOriginal = original.replace(/[^A-Za-z0-9\s]/g, '').toLowerCase();
        // find runs of TitleCase words
        const multi = s.match(/\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b/g);
        if (multi) multi.forEach(m => {
            const key = m.trim();
            const normKey = key.replace(/[^A-Za-z0-9\s]/g, '').toLowerCase();
            if (normKey && normKey !== normOriginal) {
                freq.set(key, (freq.get(key)||0)+2);
            }
        });
        // tokenise on word characters (keep apostrophes)
        const toks = (s.match(/[A-Za-z']+/g) || []);
        toks.forEach(t => {
            // Remove possessive 's or s' at the end (e.g., "Girl's" -> "Girl", "Boys'" -> "Boys")
            let clean = t.replace(/^'+|'+$/g, '');
            clean = clean.replace(/('s|s')$/i, '');
            if (!clean) return;
            const low = clean.toLowerCase();
            if (low.length < 3) return;
            if (stop.has(low)) return;
            // avoid extracting the whole aspect verbatim
            if (clean.replace(/[^A-Za-z0-9]/g, '').toLowerCase() === normOriginal.replace(/[^A-Za-z0-9]/g, '')) return;
            // prefer TitleCase tokens
            if (clean[0] === clean[0].toUpperCase() && clean.slice(1) === clean.slice(1).toLowerCase()) {
                freq.set(clean, (freq.get(clean)||0) + 3);
                return;
            }
            // morphological hint for nouns
            for (const suf of nounSuffixes) {
                if (low.endsWith(suf)) { freq.set(clean, (freq.get(clean)||0) + 2); return; }
            }
            // otherwise lightly count
            freq.set(clean, (freq.get(clean)||0) + 1);
        });
    });
    // convert map to weighted array of tokens
    const items = Array.from(freq.entries()).sort((a,b) => b[1]-a[1]);
    return items.map(x => x[0]);
}

// helper: weighted pick from an array (by position weight)
function pickWeighted(list) {
    if (!list || list.length === 0) return null;
    if (list.length === 1) return list[0];
    // higher-ranked items should be more likely: give weights decreasing linearly
    const total = list.length * (list.length + 1) / 2;
    let r = Math.floor(Math.random() * total) + 1;
    for (let i = 0; i < list.length; i++) {
        const weight = list.length - i;
        if (r <= weight) return list[i];
        r -= weight;
    }
    return list[0];
}

// Pick a suffix from the list that keeps the full name under maxLen. Returns
// an empty string when no suffix fits. The selection order is randomized so
// repeated calls don't always bias the same suffix.
function pickSuffixWithinLimit(prefix, suffixList, maxLen = NAME_MAX_LENGTH) {
    if (!suffixList || suffixList.length === 0) return '';
    // make a shallow shuffled copy
    const arr = suffixList.slice();
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        const t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    for (const s of arr) {
        const candidate = (prefix + ' ' + s).trim();
        if (candidate.length <= maxLen) return s;
    }
    return '';
}

function generateSillyName(aspects) {
    const prefixes = [
        'Captain', 'Sir', 'Lady', 'Professor', 'Grand', 'Count', 'Baron', 'Dr', 'Mr', 'Ms',
        'Duke', 'Duchess', 'Lord', 'Queen', 'King', 'Archmage', 'Squire', 'Saint', 'Master', 'Mistress',
        'Chief', 'Warden', 'Marshal', 'Admiral', 'Commander', 'Seer', 'Oracle', 'Sage', 'Witch', 'Warlock',
        'Paladin', 'Knight', 'Viceroy', 'Vizier', 'Magister', 'High Priest', 'Shaman', 'Elder', 'Guardian', 'Ranger',
        'Agent', 'Detective', 'Agent', 'Major', 'Colonel', 'General', 'Enchanter', 'Sorcerer', 'Priestess', 'Bishop',
        'Reverend', 'Father', 'Mother', 'Brother', 'Sister', 'Sensei', 'Guru', 'Maestro', 'Maestra', 'Maiden',
        'The Honorable', 'The Right', 'The Venerable', 'The Ancient', 'The Mysterious', 'The Dreaded', 'The Lost'
    ];
    const firsts = [
        'CatBoy', 'Puddle', 'Wormy', 'Soggy', 'Fluffy', 'Noodle', 'Bongo', 'Squish', 'Sneezy', 'Snark',
        'Frodo', 'Bilbo', 'Arya', 'Gandalf', 'Merlin', 'Luna', 'Nova', 'Pixel', 'Echo', 'Blaze',
        'Shadow', 'Raven', 'Willow', 'Rowan', 'Ash', 'Ember', 'Moss', 'Thorn', 'Briar', 'Maple',
        'Finn', 'Pip', 'Milo', 'Ziggy', 'Zara', 'Kai', 'Jinx', 'Trix', 'Mira', 'Vex',
        'Dax', 'Rook', 'Quill', 'Rune', 'Sable', 'Onyx', 'Jasper', 'Opal', 'Coral', 'Indigo',
        'Sprout', 'Pebble', 'Cricket', 'Wisp', 'Flick', 'Glim', 'Fizz', 'Bram', 'Tumble', 'Mirth',
        'Gizmo', 'Widget', 'Tinker', 'Patch', 'Scout', 'Rook', 'Scout', 'Midge', 'Bumble', 'Pipkin',
        'Twist', 'Fable', 'Saga', 'Quest', 'Rune', 'Echo', 'Nova', 'Vesper', 'Zephyr', 'Storm'
    ];
    const middles = [
        'Mc', 'Von', "O'", 'la', 'de', 'the', 'of', 'del', 'di', 'ap', 'bin', 'al', 'fitz', 'le', 'du',
        'da', 'van', 'ter', 'den', 'ath', 'ath-', 'ath\'', 'ath-', 'ath\'', 'ath-', 'ath\'', 'ath-', 'ath\'',
        'della', 'delle', 'dos', 'das', 'dos', 'das', 'dos', 'das', 'dos', 'das', 'dos', 'das', 'dos', 'das',
        'el', 'ibn', 'ben', 'bat', 'bar', 'san', 'saint', 'st.', 'of the', 'from', 'under', 'over', 'between'
    ];
    const cores = [
        'CatPants', 'Biscuit', 'Wobble', 'Sparkle', 'Zapper', 'Tickle', 'Wiggler', 'Larry', 'Gloop', 'Plunk',
        'Stormrider', 'Nightshade', 'Ironfoot', 'Firebrand', 'Starborn', 'Moonwhisper', 'Dawnbringer', 'Frostbeard', 'Oakenshield', 'Shadowalker',
        'Lightbringer', 'Dragonsbane', 'Wolfheart', 'Stonehelm', 'Silverleaf', 'Goldentongue', 'Swiftwind', 'Thunderfist', 'Brightblade', 'Darkwater',
        'Mistwalker', 'Sunseeker', 'Windrider', 'Frostfang', 'Ironhand', 'Quickstep', 'Deepdelver', 'Starweaver', 'Dreamer', 'Nightbreeze',
        'Foxglove', 'Hawthorne', 'Ravenshade', 'Mosscloak', 'Briarpatch', 'Emberfall', 'Pebblebrook', 'Thistledown', 'Fernvale', 'Willowisp',
        'Glimmer', 'Fizzlebang', 'Tumbleweed', 'Patchwork', 'Cricket', 'Bumblebee', 'Snickerdoodle', 'Mirthquake', 'Twilight', 'Saga',
        'Quest', 'Rune', 'Vesper', 'Zephyr', 'Storm', 'Fable', 'Gadget', 'Widget', 'Tinker', 'Sprout'
    ];
    const suffixes = [
        'III', 'Jr', 'the Bold', 'the Slightly Confused', 'the Unshaven', 'of Many Socks', 'Esq', 'the Great', 'from Next Door', 'with Hats',
        'the Wise', 'the Brave', 'the Cunning', 'the Small', 'the Tall', 'the Red', 'the Blue', 'the Green', 'the Black', 'the White',
        'the Forgotten', 'the Lost', 'the Ancient', 'the Young', 'the Old', 'the Fearless', 'the Timid', 'the Lucky', 'the Unlucky', 'the Swift',
        'the Slow', 'the Mysterious', 'the Dreaded', 'the Just', 'the Kind', 'the Cruel', 'the Merciful', 'the Relentless', 'the Patient', 'the Impatient',
        'the Wanderer', 'the Seeker', 'the Dreamer', 'the Sleeper', 'the Awakened', 'the Chosen', 'the Rejected', 'the Returned', 'the Banished', 'the Exiled',
        'of the North', 'of the South', 'of the East', 'of the West', 'of the Valley', 'of the Mountain', 'of the Lake', 'of the Forest', 'of the Sea', 'of the Desert',
        'of the Isles', 'of the Plains', 'of the River', 'of the Marsh', 'of the Deep', 'of the Sky', 'of the Stars', 'of the Sun', 'of the Moon', 'of the Eclipse',
        'Bearer of Bad News', 'Breaker of Chains', 'Friend to Ducks', 'with a Thousand Faces', 'of Infinite Jest', 'the Unpronounceable', 'the Unreadable', 'the Unstoppable', 'the Unflappable', 'the Unlikely'
    ];

    // Attempt to get keywords from provided aspects
    const kws = extractKeywords(aspects || []);

    // Choose a pattern, preferring to use a keyword when available
    const useKeyword = kws.length > 0 && Math.random() < 0.75;
    let name = '';
    if (useKeyword) {
        const k1 = pickWeighted(kws);
        const k2 = (kws.length > 1) ? pickWeighted(kws.filter(x => x !== k1)) : null;
        const pattern = Math.random();
        if (pattern < 0.35) {
            name = `${randomChoice(firsts)} ${k1}`;
        } else if (pattern < 0.6 && k2) {
            // try to pick a suffix that keeps the name short
            const base = `${elongate(randomChoice(firsts))} ${k1}`;
            const sfx = pickSuffixWithinLimit(base, suffixes, NAME_MAX_LENGTH);
            name = sfx ? `${base} ${sfx}` : base;
        } else if (pattern < 0.85) {
            const mid = randomChoice(middles);
            // If the middle part ends with a non-letter (like "O'", "ath-", etc), don't add a space
            if (/[^a-zA-Z]$/.test(mid)) {
                name = `${k1} ${mid}${randomChoice(cores)}`;
            } else {
                name = `${k1} ${mid} ${randomChoice(cores)}`;
            }
        } else {
            name = `${randomChoice(prefixes)} ${elongate(k1)}`;
        }
    } else {
        // fallback to pure silly generation
        const pattern = Math.random();
        if (pattern < 0.25) {
            name = `${randomChoice(firsts)} ${randomChoice(cores)}`;
        } else if (pattern < 0.5) {
            name = `${randomChoice(prefixes)} ${elongate(randomChoice(firsts))}`;
        } else if (pattern < 0.75) {
            const mid = randomChoice(middles);
            name = `${randomChoice(firsts)} ${mid === "O'" ? mid + randomChoice(cores) : mid + ' ' + randomChoice(cores)}`;
        } else {
            const base = `${elongate(randomChoice(firsts))} ${randomChoice(cores)}`;
            const sfx = pickSuffixWithinLimit(base, suffixes, NAME_MAX_LENGTH);
            name = sfx ? `${base} ${sfx}` : base;
        }
    }

    // Small post-processing: sometimes prepend a playful modifier
    if (Math.random() < 0.12) {
        name = `${randomChoice(['Wiggly', 'Tiny', 'Mega', 'Ultra', 'Sneaky', 'My Man,', 'His Excellency', 'Inexplicably'])} ${name}`;
    }

    return name;
}

// Centralized clone helper: deep-clone a character object, assign id, increment name royally, push to state and select it.
function cloneCharacter(orig) {
    if (!orig) return null;
    const copy = JSON.parse(JSON.stringify(orig));
    copy.id = genId('c');
    if (copy.name) copy.name = makeUniqueRoyalName(copy.name, state.cast);
    state.cast.push(copy);
    state.activeId = copy.id;
    location.hash = copy.id;
    render();
    return copy;
}

// Save/load helpers for split browser storage
function saveAspectsToBrowser() {
    try { localStorage.setItem(ASPECTS_KEY, JSON.stringify(state.groups)); }
    catch (e) { console.error('saveAspectsToBrowser failed', e); }
}
function saveCastToBrowser() {
    try { localStorage.setItem(CAST_KEY, JSON.stringify(state.cast)); }
    catch (e) { console.error('saveCastToBrowser failed', e); }
}
function saveUIToBrowser() {
    try { localStorage.setItem(UI_KEY, JSON.stringify({ activeId: state.activeId })); }
    catch (e) { console.error('saveUIToBrowser failed', e); }
}

function saveState() {
    // Persist the three logical parts. This is also called frequently from render().
    saveAspectsToBrowser();
    saveCastToBrowser();
    saveUIToBrowser();
}

function loadState() {
    // Load aspects/groups
    const a = localStorage.getItem(ASPECTS_KEY);
    if (a) {
        try { state.groups = JSON.parse(a); } catch (e) { console.error('bad aspects', e); }
    }
    // Load cast
    const c = localStorage.getItem(CAST_KEY);
    if (c) {
        try { state.cast = JSON.parse(c); } catch (e) { console.error('bad cast', e); }
    }
    // Load UI
    const u = localStorage.getItem(UI_KEY);
    if (u) {
        try { const ui = JSON.parse(u); state.activeId = ui?.activeId || null; } catch (e) { console.error('bad ui', e); }
    }
}


// DOM refs
const groupsEl = document.getElementById('groups');
const groupTemplate = document.getElementById('group-template');
const aspectTemplate = document.getElementById('aspect-template');
const activeAspects = document.getElementById('active-aspects');
const characterName = document.getElementById('character-name');
const characterDesc = document.getElementById('character-desc');
const characterColor = document.getElementById('character-color');
const castList = document.getElementById('cast-list');
const libraryAside = document.getElementById('library');
const castAside = document.getElementById('cast');
const toggleLibraryBtn = document.getElementById('toggle-library');
const toggleCastBtn = document.getElementById('toggle-cast');
const tabAspectsBtn = document.getElementById('tab-aspects');
const tabDetailsBtn = document.getElementById('tab-details');
const libraryCloseBtn = document.querySelector('#library .sidebar-close');
const castCloseBtn = document.querySelector('#cast .sidebar-close');

// init
loadState();

// Load default groups JSON and optionally merge into existing groups.
// returns the loaded array (mapped) or null on failure.
async function loadDefaults({ merge = false } = {}) {
    try {
        const resp = await fetch('./default_groups.json');
        if (!resp.ok) { console.warn('could not fetch default_groups.json'); return null }
        const data = await resp.json();
        if (!Array.isArray(data)) return null;
        const mapped = data.map(g => ({
            id: g.id || genId(),
            name: g.name || 'Unnamed',
            required: !!g.required,
            // If collapsed is not specified, default to true (collapsed)
            collapsed: g.hasOwnProperty('collapsed') ? !!g.collapsed : true,
            aspects: Array.isArray(g.aspects) ? g.aspects.slice() : []
        }));
        if (!merge) {
            state.groups = mapped;
            return mapped;
        }

        // Merge behavior: by group name (case-insensitive), add any aspects not already present.
        mapped.forEach(def => {
            const existing = state.groups.find(g => g.name.trim().toLowerCase() === (def.name || '').trim().toLowerCase());
            if (existing) {
                // add missing aspects
                def.aspects.forEach(a => {
                    if (!existing.aspects.includes(a)) existing.aspects.push(a);
                });
                // respect required/collapsed flags if not already set
                if (def.required && !existing.required) existing.required = true;
                if (def.collapsed && !existing.collapsed) existing.collapsed = true;
            } else {
                // new group, ensure unique id
                state.groups.push(Object.assign({}, def, { id: genId() }));
            }
        });

        return mapped;
    } catch (err) {
        console.warn('could not load default groups', err);
        return null;
    }
}

// If groups are empty at startup, populate from defaults.
async function ensureGroups() {
    if (Array.isArray(state.groups) && state.groups.length > 0) { render(); return }
    await loadDefaults({ merge: false });
    render();
}

ensureGroups();

// Rendering
function render() { renderGroups(); renderCast(); renderActive(); saveState(); }


function renderGroups() {
    groupsEl.innerHTML = '';
    state.groups.forEach(g => {
        const node = groupTemplate.content.cloneNode(true);
        const cont = node.querySelector('.group');
        cont.dataset.groupId = g.id;
        // reflect collapsed state from model
        if (g.collapsed) cont.classList.add('collapsed'); else cont.classList.remove('collapsed');
        cont.querySelector('.group-name').value = g.name;
        cont.querySelector('.group-required').checked = !!g.required;
        const collapseBtn = cont.querySelector('.collapse-btn');
        if (collapseBtn) collapseBtn.setAttribute('aria-expanded', (!g.collapsed).toString());
        const list = cont.querySelector('.aspect-list');
        list.dataset.groupId = g.id;
        list.dataset.droppable = 'group';
        g.aspects.forEach(a => {
            const aNode = renderAspect(a);
            list.appendChild(aNode);
        });
        groupsEl.appendChild(cont);
    });
    attachGroupHandlers();
    // ensure drag handlers are active after groups render
    attachDragHandlers();
}

function renderAspect(text, opts = {}) {
    const n = aspectTemplate.content.cloneNode(true);
    const li = n.querySelector('li.aspect');
    li.querySelector('.aspect-text').textContent = text;
    li.draggable = true;
    li.dataset.text = text;
    // edit handler
    const editBtn = li.querySelector('.edit-aspect');
    if (editBtn) {
        editBtn.title = 'Edit this aspect';
        editBtn.addEventListener('click', (ev) => {
            ev.stopPropagation();
            const current = li.dataset.text || li.querySelector('.aspect-text')?.textContent || '';
            const newText = prompt('Edit aspect', current);
            if (newText == null) return; // cancelled
            const parent = li.closest('[data-droppable]');
            if (parent) {
                const kind = parent.dataset.droppable;
                if (kind === 'group') {
                    const gid = parent.dataset.groupId;
                    const g = state.groups.find(x => x.id === gid);
                    if (g) { const idx = g.aspects.indexOf(current); if (idx >= 0) g.aspects[idx] = newText; }
                } else if (kind === 'character') {
                    const active = state.cast.find(c => c.id === state.activeId);
                    if (active) { const idx = (active.aspects || []).indexOf(current); if (idx >= 0) active.aspects[idx] = newText; }
                }
            }
            render();
        });
    }

    // delete handler
    const delBtn = li.querySelector('.delete-aspect');
    if (delBtn) {
        delBtn.title = 'Delete this aspect';
        delBtn.addEventListener('click', (ev) => {
            ev.stopPropagation();
            const current = li.dataset.text || li.querySelector('.aspect-text')?.textContent || '';
            const parent = li.closest('[data-droppable]');
            if (parent) {
                const kind = parent.dataset.droppable;
                if (kind === 'group') {
                    const gid = parent.dataset.groupId;
                    const g = state.groups.find(x => x.id === gid);
                    if (g) { g.aspects = g.aspects.filter(a => a !== current); }
                } else if (kind === 'character') {
                    const active = state.cast.find(c => c.id === state.activeId);
                    if (active) { active.aspects = (active.aspects || []).filter(a => a !== current); }
                }
            }
            render();
        });
    }

    // mobile-friendly: add-to-character button (if present in template).
    // Hide/disable when rendering aspects that already belong to the active character.
    const addBtn = li.querySelector('.add-aspect-to-character');
    if (addBtn) {
        if (opts.forCharacter) {
            // remove the button entirely for active-character aspects
            addBtn.remove();
        } else {
            addBtn.title = 'Add to active character';
            addBtn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                if (!state.activeId) document.getElementById('new-character').click();
                const active = state.cast.find(c => c.id === state.activeId);
                if (!active) return;
                active.aspects = active.aspects || [];
                if (!active.aspects.includes(text)) active.aspects.push(text);
                render();
            });
        }
    }

    return li;
}

function renderActive() {
    // If cast is empty, create a new character and set as active
    if (!state.cast || state.cast.length === 0) {
        const c = { id: genId('c'), name: '', desc: '', color: '#fff', aspects: [] };
        state.cast.push(c);
        state.activeId = c.id;
    }
    if (!state.activeId) { characterName.value = ''; characterDesc.value = ''; activeAspects.innerHTML = ''; characterColor.value = '#ffffff'; return }
    let active = state.cast.find(c => c.id === state.activeId);
    // If activeId is set but not found in cast, pick the first character
    if (!active && state.cast.length > 0) {
        active = state.cast[0];
        state.activeId = active.id;
    }
    if (!active) return;
    characterName.value = active.name || '';
    characterDesc.value = active.desc || '';
    characterColor.value = active.color || '#ffffff';
    activeAspects.innerHTML = '';
    // If the active character has no explicit name, show a suggested silly name
    if (!active.name || !active.name.trim()) {
        try {
            characterName.placeholder = "Name (\"" + generateSillyName(active.aspects || []) + "\")";
        } catch (e) { /* ignore generator errors */ }
    } else {
        // restore default placeholder when a name exists
        characterName.placeholder = 'Unnamed character';
    }
    // ensure the active list is a droppable area
    activeAspects.dataset.droppable = 'character';
    (active.aspects || []).forEach(a => activeAspects.appendChild(renderAspect(a, { forCharacter: true })));
    // reattach drag handlers so the new items are draggable
    attachDragHandlers();
    // renderAspect already hides add button for active-character aspects
}

function renderCast() {
    castList.innerHTML = '';
    state.cast.forEach(c => {
        const li = document.createElement('li');
        li.dataset.id = c.id;
        li.style.setProperty('--character-color', c.color || '#eeeeee');
        li.style.cursor = 'pointer';
        // Highlight active character
        if (c.id === state.activeId) {
            li.classList.add('active-character');
        }
        const left = document.createElement('div');
        left.textContent = c.name || '(nameless)';
        left.style.flex = '1';
        li.appendChild(left);
        const btns = document.createElement('div');
        const makeBtn = (txt, cls, fn, title) => { const b = document.createElement('button'); b.textContent = txt; b.className = cls; if (title) b.title = title; b.addEventListener('click', fn); return b }
        btns.appendChild(makeBtn('📋', 'clone', () => { cloneCharacter(c); }, 'Clone this character'));
        btns.appendChild(makeBtn('X', 'del', () => { state.cast = state.cast.filter(x => x.id !== c.id); if (state.activeId === c.id) state.activeId = null; render(); }, 'Delete this character'));
        li.appendChild(btns);
        // Make the whole list item select the character when clicked, except
        // when the click comes from the clone or delete buttons.
        li.addEventListener('click', (ev) => {
            // if the click originated on the clone or delete button, ignore
            if (ev.target.closest('button.clone') || ev.target.closest('button.del')) return;
            state.activeId = c.id; location.hash = c.id; render();
        });
        castList.appendChild(li);
    })
}

// Handlers
function attachGroupHandlers() {
    document.querySelectorAll('.group').forEach(groupEl => {
        const gid = groupEl.dataset.groupId;
        const nameInput = groupEl.querySelector('.group-name');
        const req = groupEl.querySelector('.group-required');
        const del = groupEl.querySelector('.delete-group');
        const addAspectBtn = groupEl.querySelector('.add-aspect');
        const newAspectInput = groupEl.querySelector('.new-aspect');
        const collapseBtn = groupEl.querySelector('.collapse-btn');
        if (del) del.title = 'Delete this group';
        if (addAspectBtn) addAspectBtn.title = 'Add aspect to this group';
        nameInput.addEventListener('change', e => { const g = state.groups.find(x => x.id === gid); g.name = e.target.value; render(); });
        req.addEventListener('change', e => { const g = state.groups.find(x => x.id === gid); g.required = e.target.checked; render(); });
        if (collapseBtn) collapseBtn.addEventListener('click', () => { const g = state.groups.find(x => x.id === gid); g.collapsed = !g.collapsed; render(); });
        del.addEventListener('click', e => { state.groups = state.groups.filter(x => x.id !== gid); render(); });
        addAspectBtn.addEventListener('click', () => { const val = newAspectInput.value.trim(); if (!val) return; const g = state.groups.find(x => x.id === gid); g.aspects.push(val); newAspectInput.value = ''; render(); });
    });
    attachDragHandlers();
}

function attachDragHandlers() {
    // delegate dragstart from document so newly created elements work automatically
    document.removeEventListener('dragstart', delegatedDragStart);
    document.addEventListener('dragstart', delegatedDragStart);

    // drop targets
    document.querySelectorAll('[data-droppable]').forEach(el => {
        el.removeEventListener('dragover', onDragOver);
        el.removeEventListener('drop', onDrop);
        el.removeEventListener('dragenter', onDragEnter);
        el.removeEventListener('dragleave', onDragLeave);

        el.addEventListener('dragover', onDragOver);
        el.addEventListener('drop', onDrop);
        el.addEventListener('dragenter', onDragEnter);
        el.addEventListener('dragleave', onDragLeave);
    });

    // On small screens, disable native drag-drop so users use the add button instead
    if (window.innerWidth <= 900) {
        document.querySelectorAll('[draggable="true"]').forEach(d => d.setAttribute('draggable', 'false'));
    } else {
        document.querySelectorAll('[data-droppable] [draggable="false"]').forEach(d => d.setAttribute('draggable', 'true'));
    }
}

function delegatedDragStart(e) {
    const a = e.target.closest('.aspect');
    if (!a) return;
    const list = a.closest('[data-droppable]');
    const source = list ? list.dataset.droppable : null;
    const groupId = list ? list.dataset.groupId : null;
    const text = a.dataset.text || a.querySelector('.aspect-text')?.textContent || '';
    const payload = JSON.stringify({ text, source, groupId });
    try { e.dataTransfer.setData('application/json', payload); } catch (_) { }
    e.dataTransfer.setData('text/plain', text);
    // add a dragging class to improve visuals
    a.classList.add('dragging');
}

function onDragOver(e) { e.preventDefault(); }

function onDragEnter(e) {
    const el = e.currentTarget;
    // track nested enters to avoid flicker when moving over children
    el._dragCount = (el._dragCount || 0) + 1;
    if (el._dragCount === 1 && el.classList) el.classList.add('drag-over');
}

function onDragLeave(e) {
    const el = e.currentTarget;
    el._dragCount = (el._dragCount || 1) - 1;
    if (el._dragCount <= 0) {
        el._dragCount = 0;
        if (el.classList) el.classList.remove('drag-over');
    }
}

function onDrop(e) {
    e.preventDefault();
    // remove drag-over visuals
    const el = e.currentTarget;
    if (el && el.classList) el.classList.remove('drag-over');
    // reset counter for target
    if (el) el._dragCount = 0;

    // try JSON payload first
    let payload = null;
    try { const raw = e.dataTransfer.getData('application/json'); if (raw) payload = JSON.parse(raw); } catch (_) { }
    const text = (payload && payload.text) || e.dataTransfer.getData('text/plain');
    const droppable = el.dataset.droppable;

    if (!text) return;

    if (droppable === 'character') {
        if (!state.activeId) return;
        const active = state.cast.find(c => c.id === state.activeId);
        active.aspects = active.aspects || [];
        if (!active.aspects.includes(text)) active.aspects.push(text);
        render();
    } else if (droppable === 'group') {
        const gid = el.dataset.groupId;
        const g = state.groups.find(x => x.id === gid);
        if (!g.aspects.includes(text)) g.aspects.push(text);
        render();
    }
}

// clean dragging classes when drag ends anywhere
document.addEventListener('dragend', e => { document.querySelectorAll('.dragging').forEach(x => x.classList.remove('dragging')); document.querySelectorAll('.drag-over').forEach(x => x.classList.remove('drag-over')); });

// Buttons
document.getElementById('add-group').addEventListener('click', () => { const name = document.getElementById('new-group-name').value.trim() || 'New Group'; state.groups.push({ id: genId(), name, required: false, aspects: [] }); document.getElementById('new-group-name').value = ''; render(); });

document.getElementById('new-character').addEventListener('click', () => { const c = { id: genId('c'), name: '', desc: '', color: '#fff', aspects: [] }; state.cast.push(c); state.activeId = c.id; location.hash = c.id; render(); });

document.getElementById('clone-character').addEventListener('click', () => { if (!state.activeId) return; const orig = state.cast.find(x => x.id === state.activeId); if (!orig) return; cloneCharacter(orig); });
document.getElementById('random-character').addEventListener('click', () => {
    const c = { id: genId('c'), name: '', desc: '', color: '#ffffff', aspects: [] };

    // Step 1: List of required groups
    const requiredGroups = state.groups.filter(g => g.required);

    // Step 2: Pick a number between 2 and 5 (target number of aspects)
    const target = Math.floor(Math.random() * 4) + 2; // 2..5

    // Step 3: Randomly draw-with-replacement from all groups until the list of groups is at least as large as the target
    let groupList = [...requiredGroups];
    const allGroups = state.groups.filter(g => g.aspects && g.aspects.length);
    while (groupList.length < target) {
        const g = allGroups[Math.floor(Math.random() * allGroups.length)];
        groupList.push(g);
    }

    // Always draw one other group if requiredGroups.length > target
    if (requiredGroups.length > target && allGroups.length > requiredGroups.length) {
        // Find a non-required group
        const nonRequired = allGroups.filter(g => !g.required);
        if (nonRequired.length) {
            const g = nonRequired[Math.floor(Math.random() * nonRequired.length)];
            groupList.push(g);
        }
    }

    // Step 4: Draw once from each listed group, ensuring no duplicate aspect text
    const usedAspects = new Set();
    groupList.forEach(g => {
        if (g.aspects && g.aspects.length) {
            // Filter out aspects already used
            const available = g.aspects.filter(a => !usedAspects.has(a));
            if (available.length) {
                const aspect = available[Math.floor(Math.random() * available.length)];
                c.aspects.push(aspect);
                usedAspects.add(aspect);
            }
        }
    });

    state.cast.push(c);
    state.activeId = c.id;
    location.hash = c.id;

    // If a previous random was created recently, remove it (user probably didn't care)
    try {
        const now = Date.now();
        const prev = state.lastRandom;
        if (prev && prev.id && (now - (prev.time || 0) <= RANDOM_DEBOUNCE_MS)) {
            // remove prev from cast if still present and not the one we just added
            if (prev.id !== c.id) {
                state.cast = state.cast.filter(x => x.id !== prev.id);
                // if the previous was selected, ensure activeId points to the new one
                if (state.activeId === prev.id) state.activeId = c.id;
            }
        }
        state.lastRandom = { id: c.id, time: now };
        // start visual debounce indicator
        startRandomDebounceVisual(now);
    } catch (err) { console.error('random debounce failed', err); }

    render();
});

// previously had a direct dump-cast button; functionality now exposed through Cast menu

characterName.addEventListener('input', () => { clearRandomDebounce(); const c = state.cast.find(x => x.id === state.activeId); if (!c) return; c.name = characterName.value; renderCast(); saveState(); });
characterDesc.addEventListener('input', () => { clearRandomDebounce(); const c = state.cast.find(x => x.id === state.activeId); if (!c) return; c.desc = characterDesc.value; saveState(); });
characterColor.addEventListener('input', () => { clearRandomDebounce(); const c = state.cast.find(x => x.id === state.activeId); if (!c) return; c.color = characterColor.value; renderCast(); saveState(); });

// If the user edits the active character, clear the debounce (they care about it)
function clearRandomDebounce() {
    state.lastRandom = null;
    clearRandomDebounceVisual();
}

characterName.addEventListener('change', clearRandomDebounce);
characterDesc.addEventListener('change', clearRandomDebounce);
characterColor.addEventListener('change', clearRandomDebounce);

// select via hash
window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (id) { if (state.cast.find(c => c.id === id)) state.activeId = id; render(); } });
if (location.hash.slice(1)) { const id = location.hash.slice(1); if (state.cast.find(c => c.id === id)) state.activeId = id }

// Sidebar toggle handlers (mobile)
if (toggleLibraryBtn) {
    toggleLibraryBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        libraryAside.classList.toggle('open');
        if (libraryAside.classList.contains('open')) castAside.classList.remove('open');
    });
}
if (toggleCastBtn) {
    toggleCastBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        castAside.classList.toggle('open');
        if (castAside.classList.contains('open')) libraryAside.classList.remove('open');
    });
}

// close buttons inside sidebars
if (libraryCloseBtn) libraryCloseBtn.addEventListener('click', (e) => { e.stopPropagation(); libraryAside.classList.remove('open'); });
if (castCloseBtn) castCloseBtn.addEventListener('click', (e) => { e.stopPropagation(); castAside.classList.remove('open'); });

// Tabs in active panel
if (tabAspectsBtn && tabDetailsBtn) {
    function activateTab(which) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        if (which === 'aspects') {
            tabAspectsBtn.classList.add('active');
            document.querySelector('.aspects-tab').classList.remove('hidden');
        } else {
            tabDetailsBtn.classList.add('active');
            document.querySelector('.details-tab').classList.remove('hidden');
        }
    }
    tabAspectsBtn.addEventListener('click', () => activateTab('aspects'));
    tabDetailsBtn.addEventListener('click', () => activateTab('details'));
}

// Improved: Use event propagation to detect true outside clicks for sidebars
let sidebarClickFlag = false;
function markSidebarClick() { sidebarClickFlag = true; }
if (libraryAside) libraryAside.addEventListener('mousedown', markSidebarClick);
if (castAside) castAside.addEventListener('mousedown', markSidebarClick);
if (toggleLibraryBtn) toggleLibraryBtn.addEventListener('mousedown', markSidebarClick);
if (toggleCastBtn) toggleCastBtn.addEventListener('mousedown', markSidebarClick);

document.addEventListener('mousedown', () => { sidebarClickFlag = false; }, true);
document.addEventListener('click', (e) => {
    const w = window.innerWidth;
    if (w > 900) return; // on large screens sidebars are inline
    if (sidebarClickFlag) { sidebarClickFlag = false; return; }
    // Only close if the click was not inside any sidebar or toggle
    if (libraryAside.classList.contains('open')) libraryAside.classList.remove('open');
    if (castAside.classList.contains('open')) castAside.classList.remove('open');
});

// Close sidebars with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' || e.key === 'Esc') {
        let changed = false;
        if (libraryAside.classList.contains('open')) { libraryAside.classList.remove('open'); changed = true; }
        if (castAside.classList.contains('open')) { castAside.classList.remove('open'); changed = true; }
        if (changed) e.stopPropagation();
    }
});

// local save/load (exposed via menus)
function clearBrowserCast() {
    // clear only the cast portion of browser storage and reset in-memory cast
    try { localStorage.removeItem(CAST_KEY); } catch (e) { }
    state.cast = [];
    state.activeId = null;
    state.lastRandom = null;
    render();
    alert('Cleared cast from browser storage');
}

// Visual debounce indicator for the Random button
// We'll add/remove a CSS class 'debounce-active' on the button and set a timeout
let _randomDebounceTimeout = null;
function startRandomDebounceVisual(startTime) {
    const btn = document.getElementById('random-character');
    if (!btn) return;
    // clear any existing timer
    if (_randomDebounceTimeout) { clearTimeout(_randomDebounceTimeout); _randomDebounceTimeout = null; }

    // compute remaining time and set as CSS var so the pseudo-element uses the right duration
    const now = Date.now();
    const elapsed = Math.max(0, now - (startTime || now));
    const remaining = Math.max(0, RANDOM_DEBOUNCE_MS - elapsed);
    try { btn.style.setProperty('--rb-duration', remaining + 'ms'); } catch (e) { }

    // Restart the CSS animation by removing and re-adding the class and forcing a reflow
    btn.classList.remove('debounce-active');
    // force reflow
    // eslint-disable-next-line no-unused-expressions
    void btn.offsetWidth;
    btn.classList.add('debounce-active');

    // set a timer to clear the visual after the remaining window
    _randomDebounceTimeout = setTimeout(() => { clearRandomDebounce(); }, remaining + 20);
}
function clearRandomDebounceVisual() {
    const btn = document.getElementById('random-character');
    if (btn) {
        btn.classList.remove('debounce-active');
        // force reflow to ensure any running animation is stopped
        // eslint-disable-next-line no-unused-expressions
        void btn.offsetWidth;
        try { btn.style.removeProperty('--rb-duration'); } catch (e) { }
    }
    if (_randomDebounceTimeout) { clearTimeout(_randomDebounceTimeout); _randomDebounceTimeout = null; }
}

// Inject minimal CSS for the visual (a circular border that wipes clockwise)
// and for highlighting the active character in the cast list
try {
    const style = document.createElement('style');
    style.textContent = `
        /* debounce visual: a left-to-right background wipe on the Random button. */
        #random-character.debounce-active {
            position: relative;
            overflow: hidden;
            z-index: 0;
        }
        #random-character.debounce-active::before {
            content: '';
            position: absolute;
            inset: 0;
            z-index: -1;
            background: linear-gradient(90deg, rgba(0,150,200,0.12), rgba(0,150,200,0.12));
            background-size: 100% 100%;
            background-repeat: no-repeat;
            transform-origin: left center;
            animation: rb-wipe var(--rb-duration, ${RANDOM_DEBOUNCE_MS}ms) linear forwards;
        }
        @keyframes rb-wipe { from { background-size: 100% 100%; } to { background-size: 0% 100%; } }

        /* Highlight the active character in the cast list */
        #cast-list li.active-character {
            border: 2.5px solid #1e90ff;
            border-radius: 7px;
            box-shadow: 0 0 0 2px rgba(30,144,255,0.10);
        }
    `;
    document.head.appendChild(style);
} catch (err) { /* ignore in non-DOM environments */ }

// groups storage helpers (aspects)
function saveGroupsToBrowser() { saveAspectsToBrowser(); alert('Saved groups to browser storage'); }
function clearGroupsBrowser() { try { localStorage.removeItem(ASPECTS_KEY); } catch (e) { } state.groups = []; render(); alert('Cleared groups from browser storage'); }

// menu wiring
const castMenuBtn = document.getElementById('cast-menu-btn');
const castMenu = document.getElementById('cast-menu');
castMenuBtn?.addEventListener('click', (e) => {
    // Prevent the global document click handler from immediately closing the menu
    e.stopPropagation();
    const open = castMenu.classList.toggle('hidden');
    const visible = !open; // class 'hidden' present => open===true, so visible = !open
    castMenuBtn.setAttribute('aria-expanded', (visible).toString());
    castMenu.setAttribute('aria-hidden', (!visible).toString());

    // Position the menu next to the button when it's opened. Use fixed positioning
    // so the menu appears near the viewport coordinates of the button regardless
    // of ancestor positioning. Keep it within the viewport if it would overflow.
    if (visible) {
        const rect = castMenuBtn.getBoundingClientRect();
        castMenu.style.position = 'fixed';
        castMenu.style.zIndex = '9999';
        // measure after making visible
        const mw = castMenu.offsetWidth || 200;
        const mh = castMenu.offsetHeight || 200;
        let left = rect.left;
        // clamp to viewport with 8px margin
        left = Math.min(left, window.innerWidth - mw - 8);
        left = Math.max(8, left);
        let top = rect.bottom;
        if (top + mh > window.innerHeight) top = Math.max(8, rect.top - mh);
        castMenu.style.left = left + 'px';
        castMenu.style.top = top + 'px';
    }
});
document.addEventListener('click', (e) => {
    if (!e.target.closest('.cast-actions')) {
        castMenu.classList.add('hidden'); castMenuBtn?.setAttribute('aria-expanded', 'false'); castMenu?.setAttribute('aria-hidden', 'true');
    }
    // inline-controls is used for groups header button
    if (!e.target.closest('.inline-controls')) {
        const groupsMenuBtn = document.getElementById('groups-menu-btn');
        const groupsMenu = document.getElementById('groups-menu');
        groupsMenu?.classList.add('hidden'); groupsMenuBtn?.setAttribute('aria-expanded', 'false'); groupsMenu?.setAttribute('aria-hidden', 'true');
    }
});

castMenu?.addEventListener('click', (e) => {
    // Prevent the click from bubbling to document which would close the menu
    e.stopPropagation();
    const btn = e.target.closest('.menu-item');
    if (!btn) return;
    const action = btn.dataset.action;
    if (action === 'save-browser') { saveCastToBrowser(); alert('Saved cast to browser storage'); }
    else if (action === 'clear-browser') clearBrowserCast();
    else if (action === 'save-file') {
        const blob = new Blob([JSON.stringify(state.cast, null, 2)], { type: 'application/json' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'cast.json'; a.click();
    } else if (action === 'load-file') {
        // trigger hidden file input
        const fi = document.getElementById('load-cast'); if (fi) fi.click();
    }
    // close menu
    castMenu.classList.add('hidden'); castMenuBtn?.setAttribute('aria-expanded', 'false'); castMenu?.setAttribute('aria-hidden', 'true');
});

// groups menu wiring (inline header control)
const groupsMenuBtn = document.getElementById('groups-menu-btn');
const groupsMenu = document.getElementById('groups-menu');
groupsMenuBtn?.addEventListener('click', (e) => {
    // Prevent document handler from closing the menu immediately
    e.stopPropagation();
    const open = groupsMenu.classList.toggle('hidden');
    const visible = !open;
    groupsMenuBtn.setAttribute('aria-expanded', (visible).toString());
    groupsMenu.setAttribute('aria-hidden', (!visible).toString());

    if (visible) {
        const rect = groupsMenuBtn.getBoundingClientRect();
        groupsMenu.style.position = 'fixed';
        groupsMenu.style.zIndex = '9999';
        const mw = groupsMenu.offsetWidth || 200;
        const mh = groupsMenu.offsetHeight || 200;
        let left = rect.left;
        left = Math.min(left, window.innerWidth - mw - 8);
        left = Math.max(8, left);
        let top = rect.bottom;
        if (top + mh > window.innerHeight) top = Math.max(8, rect.top - mh);
        groupsMenu.style.left = left + 'px';
        groupsMenu.style.top = top + 'px';
    }
});
groupsMenu?.addEventListener('click', (e) => {
    const btn = e.target.closest('.menu-item');
    if (!btn) return;
    const action = btn.dataset.action;
    if (action === 'save-browser') saveGroupsToBrowser();
    else if (action === 'clear-browser') clearGroupsBrowser();
    else if (action === 'save-file') {
        const blob = new Blob([JSON.stringify(state.groups, null, 2)], { type: 'application/json' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'groups.json'; a.click();
    } else if (action === 'load-file') {
        const fi = document.getElementById('load-groups'); if (fi) fi.click();
    } else if (action === 'load-defaults') {
        // merge defaults into existing groups
        loadDefaults({ merge: true }).then(() => { render(); alert('Defaults loaded and merged'); });
    }
    groupsMenu.classList.add('hidden'); groupsMenuBtn?.setAttribute('aria-expanded', 'false'); groupsMenu?.setAttribute('aria-hidden', 'true');
});

// file input handler for groups
document.getElementById('load-groups').addEventListener('change', e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = ev => { try { const data = JSON.parse(ev.target.result); if (Array.isArray(data)) { state.groups = data; render() } else alert('invalid groups file') } catch (err) { alert('bad file') } }; r.readAsText(f); });

// keep file input handler for the hidden input
document.getElementById('load-cast').addEventListener('change', e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = ev => { try { const data = JSON.parse(ev.target.result); if (Array.isArray(data)) { state.cast = data; state.activeId = data[0]?.id || null; state.lastRandom = null; render() } else alert('invalid cast file') } catch (err) { alert('bad file') } }; r.readAsText(f); });


// attach initial drag handlers post-render
setTimeout(() => attachDragHandlers(), 50);

// done
console.log('Aspect Builder ready');
