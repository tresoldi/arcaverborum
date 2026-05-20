"""Tests for the family-prefixed av_id scheme (arcaverborum.avid)."""

from __future__ import annotations

from arcaverborum import avid


def test_slugify_basic_and_folding():
    assert avid.slugify_name("Latin") == "latin"
    assert avid.slugify_name("Mandarin Chinese") == "mandarin-chinese"
    assert avid.slugify_name("Táobā") == "taoba"
    assert avid.slugify_name("Old English (ca. 450-1100)") == "old-english-ca-450-1100"
    # Empty falls back to the glottocode, then to a sentinel.
    assert avid.slugify_name("", fallback="abcd1234") == "abcd1234"
    assert avid.slugify_name("", fallback="") == "unnamed"


def test_family_codes_seeded_and_unique():
    fams = ["Indo-European", "Sino-Tibetan", "Arawakan", "Arawan", "Araucanian"]
    codes = avid.build_family_codes(fams)
    assert codes["Indo-European"] == "ine"   # seeded
    assert codes["Sino-Tibetan"] == "sit"    # seeded
    # First-three collisions ("Ara...") resolve to distinct 3-char codes.
    assert len({codes[f] for f in fams}) == len(fams)
    assert all(len(c) == 3 for c in codes.values())


def test_family_codes_biggest_first_claims_clean_code():
    # Order is honoured: the first-listed family claims the clean first-3.
    codes = avid.build_family_codes(["Nuclear Trans New Guinea", "Nuclear Torricelli"])
    assert codes["Nuclear Trans New Guinea"] == "nuc"
    assert codes["Nuclear Torricelli"] != "nuc"


def test_assign_av_ids_shape_and_collisions():
    codes = {"Indo-European": "ine"}
    varieties = [
        {"glottocode": "lati1261", "name": "Latin", "family": "Indo-European"},
        # Two same-named varieties in the same family -> Glottocode order decides.
        {"glottocode": "bbbb2222", "name": "Dup", "family": "Indo-European"},
        {"glottocode": "aaaa1111", "name": "Dup", "family": "Indo-European"},
        # Unknown family -> undetermined prefix.
        {"glottocode": "xxxx9999", "name": "Mystery", "family": "Nowhere"},
    ]
    m = avid.assign_av_ids(varieties, codes)
    assert m["lati1261"] == "ine-latin"
    # Lowest Glottocode keeps the bare slug; the next gets -2.
    assert m["aaaa1111"] == "ine-dup"
    assert m["bbbb2222"] == "ine-dup-2"
    assert m["xxxx9999"] == f"{avid.UNDETERMINED_CODE}-mystery"
    assert len(set(m.values())) == len(m)


def test_mint_av_id_incremental():
    codes = {"Indo-European": "ine"}
    taken = {"ine-latin"}
    assert avid.mint_av_id("Latin", "Indo-European", codes, taken) == "ine-latin-2"
    assert avid.mint_av_id("Oscan", "Indo-European", codes, taken) == "ine-oscan"


def test_family_codes_roundtrip(tmp_path):
    codes = {"Indo-European": "ine", "Sino-Tibetan": "sit"}
    path = tmp_path / "family_codes.csv"
    avid.write_family_codes(codes, path)
    assert avid.load_family_codes(path) == codes
