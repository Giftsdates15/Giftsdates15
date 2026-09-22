#!/usr/bin/env python3
"""
Additional test to verify verified badge propagation in profiles.
Creates two users: one verified, one not, and checks if the verified badge appears correctly.
"""
import requests
import io
from pymongo import MongoClient

# Load backend URL
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.split('=', 1)[1].strip()
            break

API_URL = f"{BASE_URL}/api"

# MongoDB connection
with open('/app/backend/.env', 'r') as f:
    for line in f:
        if line.startswith('MONGO_URL='):
            MONGO_URL = line.split('=', 1)[1].strip().strip('"')
        elif line.startswith('DB_NAME='):
            DB_NAME = line.split('=', 1)[1].strip().strip('"')

mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

print("Testing verified badge propagation...")
print("=" * 80)

def create_test_file():
    """Create a minimal valid JPEG."""
    data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\xfe(\xa2\x8a\xff\xd9'
    return io.BytesIO(data)

# Create User A (male, will be verified)
print("\n1. Creating User A (male, will be verified)...")
resp = requests.post(f"{API_URL}/auth/register", json={
    "email": "verified_male@example.com",
    "password": "SecurePass123!",
    "name": "Verified Male",
    "age": 30,
    "gender": "male",
    "interested_in": "female",
    "orientation": "straight",
    "city": "New York",
    "country": "USA",
    "birth_year": 1994,
    "birth_month": 3,
    "birth_day": 10
})
if resp.status_code == 200:
    user_a_token = resp.json()["token"]
    user_a_id = resp.json()["user"]["id"]
    print(f"✅ User A created: {user_a_id}")
else:
    print(f"❌ Failed to create User A: {resp.status_code}")
    exit(1)

# Upload verification docs for User A
print("2. Uploading verification documents for User A...")
requests.post(
    f"{API_URL}/verification/upload?kind=id",
    headers={"Authorization": f"Bearer {user_a_token}"},
    files={"file": ("id.jpg", create_test_file(), "image/jpeg")}
)
requests.post(
    f"{API_URL}/verification/upload?kind=selfie",
    headers={"Authorization": f"Bearer {user_a_token}"},
    files={"file": ("selfie.jpg", create_test_file(), "image/jpeg")}
)
print("✅ Documents uploaded")

# Get review token and approve User A
print("3. Approving User A...")
user_a_doc = db.users.find_one({"id": user_a_id})
review_token = user_a_doc["verification"]["review_token"]
resp = requests.get(f"{API_URL}/verification/review?token={review_token}&action=approve")
if "approved" in resp.text.lower():
    print("✅ User A approved and verified")
else:
    print(f"❌ Failed to approve User A")
    exit(1)

# Create User B (female, not verified)
print("\n4. Creating User B (female, not verified)...")
resp = requests.post(f"{API_URL}/auth/register", json={
    "email": "unverified_female@example.com",
    "password": "SecurePass123!",
    "name": "Unverified Female",
    "age": 28,
    "gender": "female",
    "interested_in": "male",
    "orientation": "straight",
    "city": "New York",
    "country": "USA",
    "birth_year": 1996,
    "birth_month": 7,
    "birth_day": 20
})
if resp.status_code == 200:
    user_b_token = resp.json()["token"]
    user_b_id = resp.json()["user"]["id"]
    print(f"✅ User B created: {user_b_id}")
else:
    print(f"❌ Failed to create User B: {resp.status_code}")
    exit(1)

# User B searches for profiles (should see User A with verified badge)
print("\n5. User B searching for profiles...")
resp = requests.get(f"{API_URL}/profiles", headers={"Authorization": f"Bearer {user_b_token}"})
if resp.status_code == 200:
    profiles = resp.json()
    print(f"✅ Found {len(profiles)} profiles")
    
    # Find User A in the results
    user_a_profile = next((p for p in profiles if p.get("id") == user_a_id), None)
    if user_a_profile:
        verified_status = user_a_profile.get("verified")
        print(f"\n✅ User A found in profiles!")
        print(f"   - Name: {user_a_profile.get('name')}")
        print(f"   - Verified: {verified_status}")
        
        if verified_status == True:
            print("\n✅✅✅ VERIFIED BADGE PROPAGATION WORKING! ✅✅✅")
            print("   User A appears with verified=true in GET /api/profiles")
        else:
            print(f"\n❌ ISSUE: User A has verified={verified_status} (expected True)")
    else:
        print(f"\n⚠️  User A not found in profiles (may be filtered)")
        print(f"   Total profiles returned: {len(profiles)}")
        if profiles:
            print(f"   Sample profile IDs: {[p.get('id')[:8] for p in profiles[:3]]}")
else:
    print(f"❌ Failed to get profiles: {resp.status_code}")

# Check User A's profile directly
print("\n6. Checking User A's profile directly...")
resp = requests.get(f"{API_URL}/profiles/{user_a_id}", headers={"Authorization": f"Bearer {user_b_token}"})
if resp.status_code == 200:
    profile = resp.json()
    verified_status = profile.get("verified")
    print(f"✅ User A profile retrieved")
    print(f"   - Name: {profile.get('name')}")
    print(f"   - Verified: {verified_status}")
    
    if verified_status == True:
        print("\n✅✅✅ VERIFIED BADGE IN PROFILE VIEW WORKING! ✅✅✅")
    else:
        print(f"\n❌ ISSUE: Profile has verified={verified_status} (expected True)")
else:
    print(f"❌ Failed to get profile: {resp.status_code}")

print("\n" + "=" * 80)
print("Badge propagation test completed!")
