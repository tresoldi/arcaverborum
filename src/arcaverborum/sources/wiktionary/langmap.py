"""Wiktionary language code → ISO 639-3 / Glottocode mapping."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

ISO639_1_TO_3: dict[str, str] = {
    "aa": "aar", "ab": "abk", "af": "afr", "ak": "aka", "am": "amh",
    "an": "arg", "ar": "ara", "as": "asm", "av": "ava", "ay": "aym",
    "az": "aze", "ba": "bak", "be": "bel", "bg": "bul", "bh": "bih",
    "bi": "bis", "bm": "bam", "bn": "ben", "bo": "bod", "br": "bre",
    "bs": "bos", "ca": "cat", "ce": "che", "ch": "cha", "co": "cos",
    "cr": "cre", "cs": "ces", "cu": "chu", "cv": "chv", "cy": "cym",
    "da": "dan", "de": "deu", "dv": "div", "dz": "dzo", "ee": "ewe",
    "el": "ell", "en": "eng", "eo": "epo", "es": "spa", "et": "est",
    "eu": "eus", "fa": "fas", "ff": "ful", "fi": "fin", "fj": "fij",
    "fo": "fao", "fr": "fra", "fy": "fry", "ga": "gle", "gd": "gla",
    "gl": "glg", "gn": "grn", "gu": "guj", "gv": "glv", "ha": "hau",
    "he": "heb", "hi": "hin", "ho": "hmo", "hr": "hrv", "ht": "hat",
    "hu": "hun", "hy": "hye", "hz": "her", "ia": "ina", "id": "ind",
    "ie": "ile", "ig": "ibo", "ii": "iii", "ik": "ipk", "io": "ido",
    "is": "isl", "it": "ita", "iu": "iku", "ja": "jpn", "jv": "jav",
    "ka": "kat", "kg": "kon", "ki": "kik", "kj": "kua", "kk": "kaz",
    "kl": "kal", "km": "khm", "kn": "kan", "ko": "kor", "kr": "kau",
    "ks": "kas", "ku": "kur", "kv": "kom", "kw": "cor", "ky": "kir",
    "la": "lat", "lb": "ltz", "lg": "lug", "li": "lim", "ln": "lin",
    "lo": "lao", "lt": "lit", "lu": "lub", "lv": "lav", "mg": "mlg",
    "mh": "mah", "mi": "mri", "mk": "mkd", "ml": "mal", "mn": "mon",
    "mr": "mar", "ms": "msa", "mt": "mlt", "my": "mya", "na": "nau",
    "nb": "nob", "nd": "nde", "ne": "nep", "ng": "ndo", "nl": "nld",
    "nn": "nno", "no": "nor", "nr": "nbl", "nv": "nav", "ny": "nya",
    "oc": "oci", "oj": "oji", "om": "orm", "or": "ori", "os": "oss",
    "pa": "pan", "pi": "pli", "pl": "pol", "ps": "pus", "pt": "por",
    "qu": "que", "rm": "roh", "rn": "run", "ro": "ron", "ru": "rus",
    "rw": "kin", "sa": "san", "sc": "srd", "sd": "snd", "se": "sme",
    "sg": "sag", "si": "sin", "sk": "slk", "sl": "slv", "sm": "smo",
    "sn": "sna", "so": "som", "sq": "sqi", "sr": "srp", "ss": "ssw",
    "st": "sot", "su": "sun", "sv": "swe", "sw": "swa", "ta": "tam",
    "te": "tel", "tg": "tgk", "th": "tha", "ti": "tir", "tk": "tuk",
    "tl": "tgl", "tn": "tsn", "to": "ton", "tr": "tur", "ts": "tso",
    "tt": "tat", "tw": "twi", "ty": "tah", "ug": "uig", "uk": "ukr",
    "ur": "urd", "uz": "uzb", "ve": "ven", "vi": "vie", "vo": "vol",
    "wa": "wln", "wo": "wol", "xh": "xho", "yi": "yid", "yo": "yor",
    "za": "zha", "zh": "zho", "zu": "zul",
}

PROTO_TO_GLOTTOCODE: dict[str, str] = {
    "ine-pro": "indo1319",
    "gem-pro": "germ1287",
    "gmw-pro": "west2793",
    "sla-pro": "slav1255",
    "cel-pro": "celt1248",
    "itc-pro": "ital1284",
    "ira-pro": "iran1269",
    "iir-pro": "indo1321",
    "grk-pro": "gree1276",
    "bat-pro": "balt1263",
    "trk-pro": "turk1311",
    "urj-pro": "ural1272",
    "fiu-fin-pro": "finn1317",
    "sem-pro": "semi1276",
    "ber-pro": "berb1260",
    "cau-nec-pro": "nakh1245",
    "dra-pro": "drav1251",
    "tai-pro": "taik1256",
    "mkh-pro": "aust1305",
    "poz-pro": "mala1545",
    "map-pro": "aust1307",
    "poz-oce-pro": "ocea1241",
    "poz-pol-pro": "poly1242",
    "sit-pro": "sino1245",
    "tbq-pro": "tibe1272",
    "alv-pro": "atla1278",
    "bnt-pro": "narr1281",
    "cdc-pro": "chad1250",
    "ath-pro": "atha1245",
    "sai-tup-pro": "tupi1275",
    "aus-pam-pro": "pama1250",
    "oto-pro": "otom1299",
    "azc-pro": "utoa1244",
    "mun-pro": "mund1335",
    "nai-alg-pro": "algo1256",
    "nic-pro": "atla1278",
    "cus-pro": "cush1243",
    "omv-pro": "omot1245",
    "wen-pro": "sorb1249",
    "zlw-pro": "west2289",
    "zls-pro": "sout3147",
    "zle-pro": "east2269",
    "roa-pro": "roma1334",
    "osc-pro": "sabc1235",
    "xto-pro": "tokh1241",
}


@dataclass(frozen=True, slots=True)
class LangMapping:
    iso639p3: str
    glottocode: str
    glottolog_name: str
    macroarea: str
    latitude: float | None
    longitude: float | None
    family: str


_EMPTY_MAPPING = LangMapping("", "", "", "", None, None, "")


def _load_glottolog_index(path: Path) -> dict[str, LangMapping]:
    index: dict[str, LangMapping] = {}
    if not path.exists():
        logger.warning("Glottolog file not found: %s", path)
        return index

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            iso = row.get("iso639P3code", row.get("ISO639P3code", "")).strip()
            gc = row.get("id", row.get("glottocode", row.get("Glottocode", ""))).strip()
            name = row.get("name", row.get("Name", row.get("Glottolog_Name", ""))).strip()
            macro = row.get("macroarea", row.get("Macroarea", "")).strip()
            family = row.get("family_id", row.get("Family", "")).strip()

            lat_str = row.get("latitude", row.get("Latitude", "")).strip()
            lon_str = row.get("longitude", row.get("Longitude", "")).strip()
            lat = float(lat_str) if lat_str else None
            lon = float(lon_str) if lon_str else None

            mapping = LangMapping(iso, gc, name, macro, lat, lon, family)

            if gc:
                index[gc] = mapping
            if iso:
                index[f"iso:{iso}"] = mapping

    logger.info("Loaded %d Glottolog entries", len(index))
    return index


def build_lang_mapper(
    glottolog_path: Path | None = None,
) -> Callable[[str, str], LangMapping]:
    glottolog_index: dict[str, LangMapping] = {}
    if glottolog_path:
        glottolog_index = _load_glottolog_index(glottolog_path)

    unmapped: set[str] = set()

    def resolve(wikt_code: str, wikt_name: str) -> LangMapping:
        if wikt_code in PROTO_TO_GLOTTOCODE:
            gc = PROTO_TO_GLOTTOCODE[wikt_code]
            if gc in glottolog_index:
                return glottolog_index[gc]
            return LangMapping("", gc, wikt_name, "", None, None, "")

        iso3 = wikt_code
        if len(wikt_code) == 2 and wikt_code in ISO639_1_TO_3:
            iso3 = ISO639_1_TO_3[wikt_code]

        if len(iso3) == 3:
            key = f"iso:{iso3}"
            if key in glottolog_index:
                return glottolog_index[key]
            return LangMapping(iso3, "", wikt_name, "", None, None, "")

        if wikt_code not in unmapped:
            unmapped.add(wikt_code)
            logger.debug("Unmapped Wiktionary code: %s (%s)", wikt_code, wikt_name)

        return LangMapping("", "", wikt_name, "", None, None, "")

    return resolve
