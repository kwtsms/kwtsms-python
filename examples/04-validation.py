"""
Example 04: Phone Number Validation
-------------------------------------
Validate and normalize phone numbers before sending: locally (instant, no API
call) or against the kwtSMS routing database (checks carrier support and
country activation on your account).

Use cases:
    - Clean an imported CSV before a campaign
    - Validate user input on a sign-up form
    - Check if a country is routable before attempting to send

Run:
    python examples/04-validation.py
"""

from kwtsms import KwtSMS
from kwtsms._core import normalize_phone, validate_phone_input

# ── Local validation (no API call, instant) ──────────────────────────────────

print("=== LOCAL VALIDATION (no API call) ===\n")

numbers_to_test = [
    "+965 XXXX XXXX",        # Valid Kuwait
    "0096512345678",         # Valid Kuwait (00 prefix)
    "٩٦٥XXXXXXXX",          # Arabic digits, normalized automatically
    "admin@example.com",     # Email, rejected
    "123",                   # Too short, rejected
    "1234567890123456",      # Too long (16 digits), rejected
    "call me",               # No digits, rejected
    "+1 800 555 0199",       # Valid US
    "  965XXXXXXXX  ",       # Extra whitespace, trimmed and valid
]

for number in numbers_to_test:
    valid, error, normalized = validate_phone_input(number)
    display = repr(number).ljust(30)
    if valid:
        print(f"  OK  {display} -> {normalized}")
    else:
        print(f"  ERR {display} -> {error}")

# ── Normalization examples ────────────────────────────────────────────────────

print("\n=== NORMALIZATION EXAMPLES ===\n")

raw_inputs = {
    "+965 XXXX-XXXX":  "965XXXXXXXX",
    "00965XXXXXXXX":   "965XXXXXXXX",
    "٩٦٥XXXXXXXX":    "965XXXXXXXX",  # Arabic-Indic digits
    "۹۶۵XXXXXXXX":    "965XXXXXXXX",  # Extended Arabic-Indic (Persian)
    "(965) XXXX XXXX": "965XXXXXXXX",
}

for raw, expected in raw_inputs.items():
    result = normalize_phone(raw)
    ok = result == expected
    status = "OK " if ok else "ERR"
    print(f"  {status} {raw!r:30} -> {result!r}")

# ── API validation (checks routing to carrier) ───────────────────────────────
#
# validate() calls the kwtSMS /validate/ API endpoint.
# It returns which numbers are routable on your account,
# which have format errors, and which have no route (country not activated).

print("\n=== API VALIDATION (carrier routing check) ===\n")

sms = KwtSMS.from_env()

bulk_list = [
    "965XXXXXXXX",
    "96512345678",
    "not-a-number",
    "+44 20 7946 0958",  # UK
    "00201234567890",    # Egypt (with 00 prefix)
]

report = sms.validate(bulk_list)

print(f"Total    : {len(bulk_list)}")
print(f"OK       : {len(report['ok'])}")
print(f"Error    : {len(report['er'])}")
print(f"No route : {len(report['nr'])}")

if report["rejected"]:
    print("\nLocally rejected (before API call):")
    for r in report["rejected"]:
        print(f"  {r['input']!r}: {r['error']}")

if report["ok"]:
    print("\nRoutable numbers:")
    for num in report["ok"]:
        print(f"  {num}")

if report["nr"]:
    print("\nNo route (country not activated):")
    for num in report["nr"]:
        print(f"  {num}")

if report["error"]:
    print(f"\nValidation error: {report['error']}")
