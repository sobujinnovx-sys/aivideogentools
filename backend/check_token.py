from app.core.config import settings
token = settings.REPLICATE_API_TOKEN
print(f"Token starts with: {token[:10]}...")
print(f"Token length: {len(token)}")
is_set = bool(token and token != "your_replicate_api_token_here")
print(f"Token set: {is_set}")
