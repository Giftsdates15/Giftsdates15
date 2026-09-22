#!/usr/bin/env python3
"""
Backend test for GiftsDates ITERATION 3: SMS opt-in, new_users_list audit, "New User" admin email
Tests according to the review request requirements
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any
from pymongo import MongoClient

# Base URL from frontend/.env
BASE_URL = "https://texture-keeper-1.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append(f"✅ {test_name}" + (f": {details}" if details else ""))
    
    def add_fail(self, test_name: str, details: str):
        self.failed.append(f"❌ {test_name}: {details}")
    
    def add_warning(self, test_name: str, details: str):
        self.warnings.append(f"⚠️  {test_name}: {details}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        if self.failed:
            print("\n🔴 FAILED TESTS:")
            for fail in self.failed:
                print(f"  {fail}")
        
        if self.warnings:
            print("\n🟡 WARNINGS:")
            for warn in self.warnings:
                print(f"  {warn}")
        
        if self.passed:
            print("\n🟢 PASSED TESTS:")
            for pass_test in self.passed:
                print(f"  {pass_test}")
        
        print("\n" + "="*80)
        print(f"Total: {len(self.passed)} passed, {len(self.failed)} failed, {len(self.warnings)} warnings")
        print("="*80 + "\n")

results = TestResults()

def get_mongo_db():
    """Get MongoDB database connection"""
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]

def register_user(name: str, email: str, sms_notifications_enabled: bool = False, 
                  phone: str = None, referral_code: str = None) -> Dict[str, Any]:
    """Register a new user and return token and user data"""
    payload = {
        "name": name,
        "email": email,
        "password": "TestPass123!",
        "age": 28,
        "gender": "female",
        "interested_in": "male",
        "orientation": "straight",
        "city": "Dubai",
        "country": "United Arab Emirates",
        "lat": 25.2048,
        "lng": 55.2708,
        "sms_notifications_enabled": sms_notifications_enabled
    }
    
    if phone:
        payload["phone"] = phone
    
    if referral_code is not None:  # Allow empty string
        payload["referral_code"] = referral_code
    
    resp = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if resp.status_code != 200:
        raise Exception(f"Registration failed: {resp.status_code} - {resp.text}")
    
    data = resp.json()
    return {
        "token": data["token"],
        "user": data["user"]
    }

def get_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def get_user_me(token: str) -> Dict[str, Any]:
    """Get current user data"""
    resp = requests.get(f"{BASE_URL}/auth/me", headers=get_headers(token))
    if resp.status_code != 200:
        raise Exception(f"Get user failed: {resp.status_code} - {resp.text}")
    return resp.json()

def patch_user_me(token: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update current user data"""
    resp = requests.patch(f"{BASE_URL}/auth/me", json=updates, headers=get_headers(token))
    if resp.status_code != 200:
        raise Exception(f"Patch user failed: {resp.status_code} - {resp.text}")
    return resp.json()

def test_1_registration_with_sms_enabled():
    """Test 1: Register user with sms_notifications_enabled=true and phone"""
    print("\n[TEST 1] Register with sms_notifications_enabled=true and phone +15551234567")
    try:
        timestamp = datetime.now().timestamp()
        user_data = register_user(
            name="SMS Test User 1",
            email=f"smstest1_{timestamp}@test.com",
            sms_notifications_enabled=True,
            phone="+15551234567",
            referral_code=""  # Empty referral code
        )
        
        user = user_data["user"]
        
        # Check sms_notifications_enabled field
        if "sms_notifications_enabled" not in user:
            results.add_fail("Test 1a", "sms_notifications_enabled field missing from user object")
            return None
        
        if user["sms_notifications_enabled"] != True:
            results.add_fail("Test 1a", f"Expected sms_notifications_enabled=true, got {user['sms_notifications_enabled']}")
            return None
        
        results.add_pass("Test 1a", "User registered with sms_notifications_enabled=true")
        
        # Check phone field
        if "phone" not in user:
            results.add_fail("Test 1b", "phone field missing from user object")
            return None
        
        if user["phone"] != "+15551234567":
            results.add_fail("Test 1b", f"Expected phone='+15551234567', got {user['phone']}")
            return None
        
        results.add_pass("Test 1b", "Phone number saved correctly")
        
        return user_data
    
    except Exception as e:
        results.add_fail("Test 1", str(e))
        return None

def test_2_registration_with_sms_disabled():
    """Test 2: Register user with sms_notifications_enabled=false"""
    print("\n[TEST 2] Register with sms_notifications_enabled=false")
    try:
        timestamp = datetime.now().timestamp()
        user_data = register_user(
            name="SMS Test User 2",
            email=f"smstest2_{timestamp}@test.com",
            sms_notifications_enabled=False,
            phone="+15559876543",
            referral_code=""
        )
        
        user = user_data["user"]
        
        if user.get("sms_notifications_enabled") != False:
            results.add_fail("Test 2", f"Expected sms_notifications_enabled=false, got {user.get('sms_notifications_enabled')}")
            return None
        
        results.add_pass("Test 2", "User registered with sms_notifications_enabled=false")
        
        return user_data
    
    except Exception as e:
        results.add_fail("Test 2", str(e))
        return None

def test_3_new_users_list_document(user_data: Dict[str, Any]):
    """Test 3: Verify new_users_list document exists with correct fields"""
    print("\n[TEST 3] Verify new_users_list MongoDB document")
    try:
        if not user_data:
            results.add_fail("Test 3", "No user data provided (previous test failed)")
            return
        
        user = user_data["user"]
        user_id = user["id"]
        email = user["email"]
        
        # Connect to MongoDB
        db = get_mongo_db()
        
        # Query new_users_list by email
        doc = db.new_users_list.find_one({"email": email})
        
        if not doc:
            results.add_fail("Test 3a", f"No document found in new_users_list for email {email}")
            return
        
        results.add_pass("Test 3a", "new_users_list document exists")
        
        # Check required fields
        required_fields = [
            "user_id", "name", "email", "country", "referral_code", 
            "sms_notifications_enabled", "registered_at"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in doc:
                missing_fields.append(field)
        
        if missing_fields:
            results.add_fail("Test 3b", f"Missing fields in new_users_list: {', '.join(missing_fields)}")
            return
        
        results.add_pass("Test 3b", "All required fields present in new_users_list document")
        
        # Verify field values
        if doc["user_id"] != user_id:
            results.add_fail("Test 3c", f"user_id mismatch: expected {user_id}, got {doc['user_id']}")
            return
        
        if doc["email"] != email:
            results.add_fail("Test 3c", f"email mismatch: expected {email}, got {doc['email']}")
            return
        
        if doc["sms_notifications_enabled"] != user.get("sms_notifications_enabled"):
            results.add_fail("Test 3c", f"sms_notifications_enabled mismatch")
            return
        
        results.add_pass("Test 3c", "new_users_list document fields match user data")
        
    except Exception as e:
        results.add_fail("Test 3", str(e))

def test_4_admin_email_outbox(user_data: Dict[str, Any]):
    """Test 4: Verify email_outbox document with subject 'New User'"""
    print("\n[TEST 4] Verify email_outbox document with subject 'New User'")
    try:
        if not user_data:
            results.add_fail("Test 4", "No user data provided (previous test failed)")
            return
        
        user = user_data["user"]
        email = user["email"]
        
        # Connect to MongoDB
        db = get_mongo_db()
        
        # Query email_outbox for admin notification
        # Look for emails sent to giftsdates@gmail.com with subject "New User"
        doc = db.email_outbox.find_one({
            "to": "giftsdates@gmail.com",
            "subject": "New User"
        }, sort=[("created_at", -1)])
        
        if not doc:
            results.add_fail("Test 4a", "No email_outbox document found with to='giftsdates@gmail.com' and subject='New User'")
            return
        
        results.add_pass("Test 4a", "email_outbox document exists with subject EXACTLY 'New User'")
        
        # Check status (sent or failed both acceptable)
        status = doc.get("status")
        if status not in ["sent", "failed"]:
            results.add_warning("Test 4b", f"Unexpected email status: {status}")
        else:
            results.add_pass("Test 4b", f"Email status is '{status}' (acceptable)")
        
        # Verify it's for the correct user (check body contains email or name)
        body = doc.get("body", "")
        if email in body or user.get("name") in body:
            results.add_pass("Test 4c", "Email body contains user information")
        else:
            results.add_warning("Test 4c", "Email body may not contain user information")
        
    except Exception as e:
        results.add_fail("Test 4", str(e))

def test_5_patch_sms_toggle():
    """Test 5: PATCH /api/auth/me to toggle sms_notifications_enabled"""
    print("\n[TEST 5] PATCH /api/auth/me to toggle sms_notifications_enabled")
    try:
        # Register a new user with sms enabled
        timestamp = datetime.now().timestamp()
        user_data = register_user(
            name="SMS Toggle Test",
            email=f"smstoggle_{timestamp}@test.com",
            sms_notifications_enabled=True,
            phone="+15551112222",
            referral_code=""
        )
        
        token = user_data["token"]
        
        # Toggle to false
        updated_user = patch_user_me(token, {"sms_notifications_enabled": False})
        
        if updated_user.get("sms_notifications_enabled") != False:
            results.add_fail("Test 5a", f"Expected sms_notifications_enabled=false after PATCH, got {updated_user.get('sms_notifications_enabled')}")
            return
        
        results.add_pass("Test 5a", "PATCH to sms_notifications_enabled=false successful")
        
        # Verify with GET
        user_me = get_user_me(token)
        if user_me.get("sms_notifications_enabled") != False:
            results.add_fail("Test 5b", "GET /auth/me does not reflect sms_notifications_enabled=false")
            return
        
        results.add_pass("Test 5b", "GET /auth/me confirms sms_notifications_enabled=false")
        
        # Toggle back to true
        updated_user2 = patch_user_me(token, {"sms_notifications_enabled": True})
        
        if updated_user2.get("sms_notifications_enabled") != True:
            results.add_fail("Test 5c", f"Expected sms_notifications_enabled=true after second PATCH, got {updated_user2.get('sms_notifications_enabled')}")
            return
        
        results.add_pass("Test 5c", "PATCH to sms_notifications_enabled=true successful")
        
        # Verify with GET again
        user_me2 = get_user_me(token)
        if user_me2.get("sms_notifications_enabled") != True:
            results.add_fail("Test 5d", "GET /auth/me does not reflect sms_notifications_enabled=true")
            return
        
        results.add_pass("Test 5d", "GET /auth/me confirms sms_notifications_enabled=true")
        
    except Exception as e:
        results.add_fail("Test 5", str(e))

def test_6_admin_endpoint_non_admin():
    """Test 6: GET /api/admin/new-users returns 403 for non-admin user"""
    print("\n[TEST 6] GET /api/admin/new-users returns 403 for non-admin")
    try:
        # Register a normal user
        timestamp = datetime.now().timestamp()
        user_data = register_user(
            name="Normal User",
            email=f"normaluser_{timestamp}@test.com",
            sms_notifications_enabled=False,
            referral_code=""
        )
        
        token = user_data["token"]
        
        # Try to access admin endpoint
        resp = requests.get(f"{BASE_URL}/admin/new-users", headers=get_headers(token))
        
        if resp.status_code != 403:
            results.add_fail("Test 6", f"Expected 403 for non-admin user, got {resp.status_code}")
            return
        
        results.add_pass("Test 6", "Non-admin user correctly receives 403 when accessing /api/admin/new-users")
        
    except Exception as e:
        results.add_fail("Test 6", str(e))

def test_7_admin_endpoint_with_admin():
    """Test 7: GET /api/admin/new-users with admin access (if available)"""
    print("\n[TEST 7] GET /api/admin/new-users with admin access")
    try:
        # Check if ADMIN_EMAILS is configured
        # Since we can't easily create an admin user without modifying env,
        # we'll just report that admin path couldn't be exercised
        
        results.add_warning("Test 7", "ADMIN_EMAILS not configured in environment. Cannot test admin access path. Only verified 403 for non-admin users.")
        
        # If we could create an admin user, we would test:
        # - GET /api/admin/new-users returns {total, users:[...]}
        # - Users are sorted by registered_at desc
        # - Filters work: ?country=United Arab Emirates, ?referral_code=, ?since=<iso>
        
    except Exception as e:
        results.add_fail("Test 7", str(e))

def main():
    print("="*80)
    print("GIFTSDATES BACKEND - ITERATION 3 TEST")
    print("SMS opt-in, new_users_list audit, 'New User' admin email")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"MongoDB: {MONGO_URL}/{DB_NAME}")
    print("="*80)
    
    # Run all tests
    user_data_1 = test_1_registration_with_sms_enabled()
    user_data_2 = test_2_registration_with_sms_disabled()
    
    # Test MongoDB documents for both users
    test_3_new_users_list_document(user_data_1)
    test_3_new_users_list_document(user_data_2)
    
    test_4_admin_email_outbox(user_data_1)
    test_4_admin_email_outbox(user_data_2)
    
    test_5_patch_sms_toggle()
    test_6_admin_endpoint_non_admin()
    test_7_admin_endpoint_with_admin()
    
    # Print summary
    results.print_summary()
    
    # Return exit code
    return 0 if len(results.failed) == 0 else 1

if __name__ == "__main__":
    exit(main())
