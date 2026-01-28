"""
Test script for contact information extraction improvements.
Tests the new phone number and email validation logic.
"""
# -*- coding: utf-8 -*-

import sys
import io
# Fix Windows console encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, r'c:\resume-grader')

from parser_engine.extractor import _is_valid_indian_phone, _is_valid_email, find_contact_info

print("=" * 60)
print("Testing Phone Number Validation")
print("=" * 60)

# Valid phone numbers
valid_phones = [
    "9876543210",
    "+919876543210",
    "+91 9876543210",
    "+91-9876543210",
    "7234567890",
    "8123456789",
    "6987654321",
]

print("\n✅ VALID Phone Numbers (should all pass):")
for phone in valid_phones:
    result = _is_valid_indian_phone(phone)
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"  {status}: {phone}")

# Invalid phone numbers (should be rejected)
invalid_phones = [
    "2020",              # Year
    "123456",            # Too short
    "5876543210",        # Starts with 5 (invalid)
    "12345678901",       # Too long
    "98765",             # Too short
    "4567891234",        # Starts with 4 (invalid)
    "+1234567890",       # Wrong country code
]

print("\n❌ INVALID Phone Numbers (should all be rejected):")
for phone in invalid_phones:
    result = _is_valid_indian_phone(phone)
    status = "✓ PASS (rejected)" if not result else "✗ FAIL (accepted)"
    print(f"  {status}: {phone}")

print("\n" + "=" * 60)
print("Testing Email Validation")
print("=" * 60)

# Valid emails
valid_emails = [
    "test@example.com",
    "user.name@company.co.in",
    "first+last@domain.org",
    "email123@test.net",
    "contact@mysite.io",
    "hello@world.tech",
]

print("\n✅ VALID Emails (should all pass):")
for email in valid_emails:
    result = _is_valid_email(email)
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"  {status}: {email}")

# Invalid emails
invalid_emails = [
    "@example.com",           # Missing local part
    "test@",                  # Missing domain
    "test..user@example.com", # Double dots
    "test@domain",            # Missing TLD
    ".test@example.com",      # Starts with dot
    "test@example.com.",      # Ends with dot
    "test @example.com",      # Space in email
]

print("\n❌ INVALID Emails (should all be rejected):")
for email in invalid_emails:
    result = _is_valid_email(email)
    status = "✓ PASS (rejected)" if not result else "✗ FAIL (accepted)"
    print(f"  {status}: {email}")

print("\n" + "=" * 60)
print("Testing Contact Extraction from Sample Text")
print("=" * 60)

sample_resume_text = """
JOHN DOE
Email: john.doe@example.com
Phone: +91 9876543210

EXPERIENCE
Software Engineer at Tech Corp (2020-2023)
Contact: 2020 was a great year
Page 123 of the report

EDUCATION
B.Tech in Computer Science
Year: 2019

CONTACT
Alternative Email: johndoe123@gmail.com
LinkedIn: linkedin.com/in/johndoe
GitHub: github.com/johndoe
Mobile: 8765432109
"""

print("\nSample Resume Text:")
print("-" * 60)
print(sample_resume_text)
print("-" * 60)

contact_info = find_contact_info(sample_resume_text)

print("\n📧 Extracted Emails:")
for email in contact_info.get("emails", []):
    print(f"  - {email}")

print("\n📱 Extracted Phone Numbers:")
for phone in contact_info.get("phones", []):
    print(f"  - {phone}")

print("\n🔗 LinkedIn:", contact_info.get("linkedin", "Not found"))
print("🔗 GitHub:", contact_info.get("github", "Not found"))

print("\n" + "=" * 60)
print("Expected Results:")
print("=" * 60)
print("✓ Should extract 2 emails: john.doe@example.com, johndoe123@gmail.com")
print("✓ Should extract 2 phone numbers: +919876543210, +918765432109")
print("✓ Should NOT extract: 2020, 123, 2019 (these are years/page numbers)")
print("✓ Phone numbers should be normalized with +91 prefix")
print("=" * 60)

# Summary
extracted_emails = len(contact_info.get("emails", []))
extracted_phones = len(contact_info.get("phones", []))

print(f"\n📊 Summary:")
print(f"  Emails extracted: {extracted_emails} (expected: 2)")
print(f"  Phones extracted: {extracted_phones} (expected: 2)")

if extracted_emails == 2 and extracted_phones == 2:
    print("\n🎉 All tests PASSED!")
else:
    print("\n⚠️ Some tests may need review")
