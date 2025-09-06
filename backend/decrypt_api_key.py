#!/usr/bin/env python3
"""
Utility script to decrypt API key from database for testing.
"""
import sys
sys.path.append('/Users/abhishek/Documents/GitHub/genailytics-consulting/strataAI/backend')

from app.core.encryption import encryption_service

# Encrypted key from database
encrypted_key = "Z0FBQUFBQm90eFdaVVBySEI3M0REUDFIdk9fWVc0Z2lrSl9qUHFtX3RMX3ZHNXNvMUo5bDBHcjlxeGdqVVlpVkZnRTdXMk0yNDI3SUVndjlET0tWMk9rYTI4UHRkc2Q3d1FtWDlQbmVURG13N3VUcmFFb1NESUJBQzFuWVFDUDhtUVhSXzZUZWhoRGlnTFRHZWVhLS1ObmlJV0ltSnhHbERndmZFUDhydExrVzM2QXROV0Y1T2hZVi1EQnVITEtWTVNtV1E4djhmS29lQ2tRZm56S2Z0OERKNVdLZ2hFWjJKVXB4cVFBS2ZWbzZ3N1Z5YnlDT01FaWR2bHB0VW5JcHo3bGFVNWU3M05oX19EQmpQZVQzVGdiWFFwbUpwRE40TDFKaWV6TnRpZzVORTlpRGZPY1BjNzA9"

try:
    decrypted_key = encryption_service.decrypt_api_key(encrypted_key)
    print(decrypted_key)
except Exception as e:
    print(f"Error decrypting key: {e}", file=sys.stderr)
    sys.exit(1)
