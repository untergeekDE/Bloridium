

# --- sd_filename: SD-sichere Dateinamen per Konversion (2026-11-20) ------------

def test_sd_filename_sanitizes_like_manifest():
    from bloridium import qpat
    # same convention as the previous RF dataset naming (rf100 names stay compatible)
    assert qpat.sd_filename("A001", "JMX jun.") == "A001_JMX_jun.qpat"
    assert qpat.sd_filename("A093", "Dirty Bass     T") == "A093_Dirty_Bass_____T.qpat"
    assert qpat.sd_filename("A096", "Q-rious?     WMF") == "A096_Q-rious_____WMF.qpat"
    assert qpat.sd_filename("A043", "SH Power") == "A043_SH_Power.qpat"
    # leer/only-special -> loc-Fallback
    assert qpat.sd_filename("A050", "...") == "A050_A050.qpat"
    assert qpat.sd_filename("A050", "") == "A050_A050.qpat"
    # never spaces, never special characters, always .qpat — safe for device-side paths
    for name in ("JMX jun.", "  spaced  out  ", "ümlaut ß", "a/b\\c:d", "..dots.."):
        fn = qpat.sd_filename("A007", name)
        assert " " not in fn and fn.endswith(".qpat") and fn.startswith("A007_")
        assert all(c.isalnum() or c in "-_." for c in fn)
