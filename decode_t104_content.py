import base64
import json

# The Base64 encoded content from the response
content_b64 = "eyJwYXNzd29yZERlcyI6IlJnaGFmUmdMQ25iLzhSZWpjRnh3dUZsSnNNZTVQZS9HVDZpMGlNWEs4NkY0ZGJZM1NwQ3VOcmNGU0daQ3VtRkhobkt3QzJDNUkyVGlDKy9UTmUwL3AzMU5Ia2Fja3dMbzVlTU03a25Da1A0VHQ2WFR4ZEExc3g4aEZGUDFiRU1pQ09od2Z5K1VGUVp3aE0xNlYrTFdJekcydjFNSnpzc25Zd2hXY0hMaks0MkNiOVRDUXdHSWcvTlZQUWFxUyt4VVhOMDNwMkpHcE5paG5oUEpINWR3ekNXVG1XbUJ3bmR1eE55WGQ5RW9Qcks4SzVvL2N1ZnExS29ocXhjSTZKa0QrWDZKdENXdXpyRGFiNmsvd0hyUWNBbkk3amo3TmRHbEd3RFlPdXBEV3ovRVRaa0FnL0pDdExxQkYxcHJicHFXQS9kVHNVYVpiY0FUMnVKeE5TTkkvUT09Iiwic2lnbiI6ImZGTnZlbDJkZ2ZHNVZaTUQwYWZyLW54RHJvaTVhcXV0bUNWdURraFNkckNlYmFkMTdHWUhsZHlFTzVsOGFvZ1RRdjFSRUVCRWw1OWpKT3FCSEJya2NkSWxucmJrUEZkZk4yNlNxdERuWkdRbElVazhGSmNXUmgxS19tcWNBendKeElTMUVEWDZDWU5sNzd2RjBpS1dYVnZIZmJCMjhKNHhhWG5FZGc3ZVZCUVlOVEhXRE1HOHFvN2F2RUlxMjNFZzZGR1dKVG94WFdjUUdFQ3duTmViQ3JzTWdRMWZXYlNRTU41UHoxbDFkUUl1MXo3aWk5OGZTcW52Y0YzczVrRnBfUEk2M3h0dmExVXJOTng1bGhpbUEzb1AwbVE0T3VhN0Q4V2UzYWVFbVBjYThYTE9nS3l6UjRYeEZIXzk5M21tejE4QVJralNvQmRMQWdzSUJ3NjEzQSJ9"

try:
    # Decode Base64
    decoded = base64.b64decode(content_b64).decode('utf-8')
    print("=" * 80)
    print("DECODED CONTENT (raw):")
    print("=" * 80)
    print(decoded)
    print()

    # Parse JSON
    data = json.loads(decoded)
    print("=" * 80)
    print("PARSED JSON:")
    print("=" * 80)
    print(json.dumps(data, indent=2))
    print()
    print(f"passwordDes length: {len(data['passwordDes'])}")
    print(f"passwordDes (first 100 chars): {data['passwordDes'][:100]}")
    print()
    print(f"sign length: {len(data['sign'])}")
    print(f"sign (first 100 chars): {data['sign'][:100]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
