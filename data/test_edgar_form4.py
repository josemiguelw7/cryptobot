"""Offline tests for data/edgar_form4.py (no network). charter_v2 s5.1."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgar_form4 as E

def doc(txdate, code):
    return f"""junk<ownershipDocument><aff10b5One>0</aff10b5One>
<issuer><issuerCik>0000001</issuerCik><issuerName>ACME</issuerName>
<issuerTradingSymbol>ACME</issuerTradingSymbol></issuer>
<reportingOwner><reportingOwnerId><rptOwnerCik>99</rptOwnerCik>
<rptOwnerName>DOE JANE</rptOwnerName></reportingOwnerId>
<reportingOwnerRelationship><isOfficer>1</isOfficer><officerTitle>CFO</officerTitle>
</reportingOwnerRelationship></reportingOwner>
<nonDerivativeTable><nonDerivativeTransaction>
<transactionDate><value>{txdate}</value></transactionDate>
<transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>1000</value></transactionShares>
<transactionPricePerShare><value>12.5</value></transactionPricePerShare>
</transactionAmounts></nonDerivativeTransaction></nonDerivativeTable>
</ownershipDocument>junk"""

f = "edgar/data/1/0000000001-26-000001.txt"
# 1. a purchase is captured, keyed by FILED date, tx_date kept separately
r = E.parse(doc("2026-09-15", "P"), "2026-09-17", f)
assert len(r) == 1 and r[0][0] == "2026-09-17" and r[0][11] == "2026-09-15"
assert r[0][3] == "ACME" and r[0][10] == "CFO" and r[0][13] == "1000"
# 2. a SALE is ignored
assert E.parse(doc("2026-09-15", "S"), "2026-09-17", f) == []
# 3. the lookahead guard FIRES on a purchase dated after publication
bad = E.parse(doc("2026-09-20", "P"), "2026-09-17", f)
try:
    for x in bad:
        assert x[11] <= x[0], "lookahead"
    raise SystemExit("FAIL: guard did not fire")
except AssertionError:
    pass
print("test_edgar_form4: PASS (3/3)")
