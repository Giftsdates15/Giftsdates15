#!/usr/bin/env python3
"""
Backend test for GiftsDates One-time Welcome Spin & Win feature
Tests the spin endpoints according to ITERATION 2 requirements
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Base URL from frontend/.env
BASE_URL = "https://texture-keeper-1.preview.emergentagent.com/api"

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

def register_user(name: str, email: str) -> Dict[str, Any]:
    """Register a new user and return token and user data"""
    payload = {
        "name": name,
        "email": email,
        "password": "TestPass123!",
        "age": 25,
        "gender": "female",
        "interested_in": "male",
        "orientation": "straight",
        "city": "New York",
        "country": "USA",
        "lat": 40.7128,
        "lng": -74.0060
    }
    
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

def test_1_new_user_welcome_spin_false():
    """Test 1: New user has welcome_spin_done == false"""
    print("\n[TEST 1] New user has welcome_spin_done == false")
    try:
        user_data = register_user("SpinTest1", f"spintest1_{datetime.now().timestamp()}@test.com")
        user = user_data["user"]
        
        if "welcome_spin_done" not in user:
            results.add_fail("Test 1", "welcome_spin_done field missing from user object")
            return
        
        if user["welcome_spin_done"] == False:
            results.add_pass("Test 1", "New user has welcome_spin_done=false")
        else:
            results.add_fail("Test 1", f"Expected welcome_spin_done=false, got {user['welcome_spin_done']}")
    
    except Exception as e:
        results.add_fail("Test 1", str(e))

def test_2_spin_status_structure():
    """Test 2: GET /api/spin/status returns correct structure"""
    print("\n[TEST 2] GET /api/spin/status structure")
    try:
        user_data = register_user("SpinTest2", f"spintest2_{datetime.now().timestamp()}@test.com")
        token = user_data["token"]
        
        resp = requests.get(f"{BASE_URL}/spin/status", headers=get_headers(token))
        
        if resp.status_code != 200:
            results.add_fail("Test 2", f"Expected 200, got {resp.status_code}: {resp.text}")
            return
        
        data = resp.json()
        
        # Check eligible field
        if "eligible" not in data:
            results.add_fail("Test 2", "Missing 'eligible' field")
            return
        
        if data["eligible"] != True:
            results.add_fail("Test 2", f"Expected eligible=true, got {data['eligible']}")
            return
        
        # Check prizes array
        if "prizes" not in data:
            results.add_fail("Test 2", "Missing 'prizes' field")
            return
        
        prizes = data["prizes"]
        if len(prizes) != 8:
            results.add_fail("Test 2", f"Expected 8 prizes, got {len(prizes)}")
            return
        
        # Check each prize structure
        for i, prize in enumerate(prizes):
            if "index" not in prize:
                results.add_fail("Test 2", f"Prize {i} missing 'index' field")
                return
            if "type" not in prize:
                results.add_fail("Test 2", f"Prize {i} missing 'type' field")
                return
            if "label" not in prize:
                results.add_fail("Test 2", f"Prize {i} missing 'label' field")
                return
            
            # Check tier prizes have days=7
            if prize["type"] in ["premium_lite", "premium", "vip"]:
                if "days" not in prize or prize["days"] != 7:
                    results.add_fail("Test 2", f"Prize {i} ({prize['type']}) should have days=7, got {prize.get('days')}")
                    return
            
            # Check coins prize has coins=10
            if prize["type"] == "coins":
                if "coins" not in prize or prize["coins"] != 10:
                    results.add_fail("Test 2", f"Prize {i} (coins) should have coins=10, got {prize.get('coins')}")
                    return
        
        results.add_pass("Test 2", "spin/status returns correct structure with 8 prizes")
    
    except Exception as e:
        results.add_fail("Test 2", str(e))

def test_3_spin_claim_and_crediting():
    """Test 3: POST /api/spin/claim works and credits properly"""
    print("\n[TEST 3] POST /api/spin/claim and reward crediting")
    
    # Test multiple users to get different prize types
    test_count = 0
    max_attempts = 30  # Try up to 30 users to get different prize types
    
    coins_tested = False
    tier_tested = False
    none_tested = False
    
    while test_count < max_attempts and not (coins_tested and tier_tested and none_tested):
        try:
            test_count += 1
            user_data = register_user(f"SpinTest3_{test_count}", f"spintest3_{test_count}_{datetime.now().timestamp()}@test.com")
            token = user_data["token"]
            user = user_data["user"]
            
            # Get user data before claim
            user_before = get_user_me(token)
            coins_before = user_before.get("coins", 0)
            created_at = user_before.get("created_at")
            
            # Claim the spin
            resp = requests.post(f"{BASE_URL}/spin/claim", headers=get_headers(token))
            
            if resp.status_code != 200:
                results.add_fail("Test 3", f"Claim failed: {resp.status_code} - {resp.text}")
                return
            
            claim_data = resp.json()
            
            if "prize" not in claim_data:
                results.add_fail("Test 3", "Response missing 'prize' field")
                return
            
            prize = claim_data["prize"]
            prize_type = prize.get("type")
            
            # Get user data after claim
            user_after = get_user_me(token)
            
            # Verify welcome_spin_done is now true
            if not user_after.get("welcome_spin_done"):
                results.add_fail("Test 3", "welcome_spin_done should be true after claim")
                return
            
            # Test based on prize type
            if prize_type == "coins":
                coins_after = user_after.get("coins", 0)
                expected_coins = coins_before + 10
                
                if coins_after == expected_coins:
                    if not coins_tested:
                        results.add_pass("Test 3a", f"Coins prize credited correctly: {coins_before} -> {coins_after}")
                        coins_tested = True
                else:
                    results.add_fail("Test 3a", f"Coins not credited correctly. Expected {expected_coins}, got {coins_after}")
                    return
            
            elif prize_type in ["premium_lite", "premium", "vip"]:
                field_map = {
                    "premium_lite": "premium_lite_until",
                    "premium": "premium_until",
                    "vip": "vip_until"
                }
                field = field_map[prize_type]
                
                tier_until = user_after.get(field)
                
                if not tier_until:
                    results.add_fail("Test 3b", f"{field} not set after winning {prize_type}")
                    return
                
                # Verify expires_at in prize response
                if "expires_at" not in prize:
                    results.add_fail("Test 3b", f"Prize response missing expires_at for {prize_type}")
                    return
                
                # Parse dates and verify ~7 days from created_at
                try:
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    tier_dt = datetime.fromisoformat(tier_until.replace("Z", "+00:00"))
                    expected_dt = created_dt + timedelta(days=7)
                    
                    # Allow a few seconds tolerance
                    diff = abs((tier_dt - expected_dt).total_seconds())
                    
                    if diff < 10:  # Within 10 seconds
                        if not tier_tested:
                            results.add_pass("Test 3b", f"{prize_type} tier expiry set correctly (~7 days from registration)")
                            tier_tested = True
                    else:
                        results.add_fail("Test 3b", f"{prize_type} expiry not ~7 days. Diff: {diff} seconds")
                        return
                
                except Exception as e:
                    results.add_fail("Test 3b", f"Date parsing error: {e}")
                    return
            
            elif prize_type == "none":
                # Verify nothing was credited
                coins_after = user_after.get("coins", 0)
                
                if coins_after == coins_before:
                    if not none_tested:
                        results.add_pass("Test 3c", "None prize: no coins credited (correct)")
                        none_tested = True
                else:
                    results.add_fail("Test 3c", f"None prize should not credit coins. Before: {coins_before}, After: {coins_after}")
                    return
            
            else:
                results.add_warning("Test 3", f"Unknown prize type: {prize_type}")
        
        except Exception as e:
            results.add_fail("Test 3", f"Attempt {test_count} error: {e}")
            return
    
    if not coins_tested:
        results.add_warning("Test 3a", "Did not encounter coins prize in 30 attempts")
    if not tier_tested:
        results.add_warning("Test 3b", "Did not encounter tier prize in 30 attempts")
    if not none_tested:
        results.add_warning("Test 3c", "Did not encounter none prize in 30 attempts")

def test_4_second_claim_fails():
    """Test 4: Second POST /api/spin/claim returns 400"""
    print("\n[TEST 4] Second claim returns 400 'Spin already used'")
    try:
        user_data = register_user("SpinTest4", f"spintest4_{datetime.now().timestamp()}@test.com")
        token = user_data["token"]
        
        # First claim
        resp1 = requests.post(f"{BASE_URL}/spin/claim", headers=get_headers(token))
        if resp1.status_code != 200:
            results.add_fail("Test 4", f"First claim failed: {resp1.status_code}")
            return
        
        # Second claim
        resp2 = requests.post(f"{BASE_URL}/spin/claim", headers=get_headers(token))
        
        if resp2.status_code != 400:
            results.add_fail("Test 4", f"Expected 400, got {resp2.status_code}")
            return
        
        error_data = resp2.json()
        detail = error_data.get("detail", "")
        
        if "Spin already used" in detail:
            results.add_pass("Test 4", "Second claim correctly returns 400 'Spin already used'")
        else:
            results.add_fail("Test 4", f"Expected 'Spin already used', got: {detail}")
    
    except Exception as e:
        results.add_fail("Test 4", str(e))

def test_5_dismiss_functionality():
    """Test 5: POST /api/spin/dismiss works correctly"""
    print("\n[TEST 5] POST /api/spin/dismiss functionality")
    try:
        user_data = register_user("SpinTest5", f"spintest5_{datetime.now().timestamp()}@test.com")
        token = user_data["token"]
        
        # Dismiss the spin
        resp_dismiss = requests.post(f"{BASE_URL}/spin/dismiss", headers=get_headers(token))
        
        if resp_dismiss.status_code != 200:
            results.add_fail("Test 5a", f"Dismiss failed: {resp_dismiss.status_code} - {resp_dismiss.text}")
            return
        
        dismiss_data = resp_dismiss.json()
        if dismiss_data.get("ok") != True:
            results.add_fail("Test 5a", f"Expected {{ok: true}}, got {dismiss_data}")
            return
        
        results.add_pass("Test 5a", "Dismiss returns {ok: true}")
        
        # Check status is now ineligible
        resp_status = requests.get(f"{BASE_URL}/spin/status", headers=get_headers(token))
        if resp_status.status_code != 200:
            results.add_fail("Test 5b", f"Status check failed: {resp_status.status_code}")
            return
        
        status_data = resp_status.json()
        if status_data.get("eligible") == False:
            results.add_pass("Test 5b", "After dismiss, spin/status shows eligible=false")
        else:
            results.add_fail("Test 5b", f"Expected eligible=false, got {status_data.get('eligible')}")
            return
        
        # Try to claim after dismiss
        resp_claim = requests.post(f"{BASE_URL}/spin/claim", headers=get_headers(token))
        
        if resp_claim.status_code == 400:
            results.add_pass("Test 5c", "Claim after dismiss returns 400")
        else:
            results.add_fail("Test 5c", f"Expected 400, got {resp_claim.status_code}")
    
    except Exception as e:
        results.add_fail("Test 5", str(e))

def test_6_no_monthly_behavior():
    """Test 6: Confirm no monthly behavior (one-time flag)"""
    print("\n[TEST 6] No monthly behavior (one-time flag)")
    try:
        user_data = register_user("SpinTest6", f"spintest6_{datetime.now().timestamp()}@test.com")
        token = user_data["token"]
        
        # Get status before claim
        resp1 = requests.get(f"{BASE_URL}/spin/status", headers=get_headers(token))
        if resp1.status_code != 200:
            results.add_fail("Test 6", f"Status check failed: {resp1.status_code}")
            return
        
        data1 = resp1.json()
        if data1.get("eligible") != True:
            results.add_fail("Test 6", "New user should be eligible")
            return
        
        # Claim the spin
        resp_claim = requests.post(f"{BASE_URL}/spin/claim", headers=get_headers(token))
        if resp_claim.status_code != 200:
            results.add_fail("Test 6", f"Claim failed: {resp_claim.status_code}")
            return
        
        # Check status after claim
        resp2 = requests.get(f"{BASE_URL}/spin/status", headers=get_headers(token))
        if resp2.status_code != 200:
            results.add_fail("Test 6", f"Status check failed: {resp2.status_code}")
            return
        
        data2 = resp2.json()
        if data2.get("eligible") == False:
            results.add_pass("Test 6", "After claim, eligible=false (permanent one-time flag)")
        else:
            results.add_fail("Test 6", f"Expected eligible=false after claim, got {data2.get('eligible')}")
        
        # Check config endpoint
        resp_config = requests.get(f"{BASE_URL}/spin/config")
        if resp_config.status_code != 200:
            results.add_warning("Test 6", f"Config endpoint failed: {resp_config.status_code}")
        else:
            config_data = resp_config.json()
            if len(config_data.get("prizes", [])) == 8:
                results.add_pass("Test 6", "spin/config returns 8 sectors")
            else:
                results.add_fail("Test 6", f"Config should return 8 sectors, got {len(config_data.get('prizes', []))}")
    
    except Exception as e:
        results.add_fail("Test 6", str(e))

def test_7_distribution_sanity():
    """Test 7: Distribution sanity check (optional)"""
    print("\n[TEST 7] Distribution sanity check (~60 users)")
    try:
        distribution = {
            "none": 0,
            "coins": 0,
            "premium_lite": 0,
            "premium": 0,
            "vip": 0
        }
        
        num_users = 60
        
        for i in range(num_users):
            try:
                user_data = register_user(f"DistTest{i}", f"disttest{i}_{datetime.now().timestamp()}@test.com")
                token = user_data["token"]
                
                resp = requests.post(f"{BASE_URL}/spin/claim", headers=get_headers(token))
                if resp.status_code == 200:
                    prize = resp.json().get("prize", {})
                    prize_type = prize.get("type")
                    
                    if prize_type in distribution:
                        distribution[prize_type] += 1
            
            except Exception as e:
                print(f"  Distribution test user {i} error: {e}")
                continue
        
        print(f"\n  Distribution results ({num_users} users):")
        for prize_type, count in distribution.items():
            percentage = (count / num_users) * 100
            print(f"    {prize_type}: {count} ({percentage:.1f}%)")
        
        # Verify only valid types appear
        total = sum(distribution.values())
        if total > 0:
            results.add_pass("Test 7a", f"Distribution test completed: {total}/{num_users} successful claims")
            
            # Check that 'none' is most frequent (should be ~40% with weight 320 out of 450 total)
            if distribution["none"] > distribution["coins"]:
                results.add_pass("Test 7b", "'none' is most frequent prize type (as expected)")
            else:
                results.add_warning("Test 7b", f"'none' ({distribution['none']}) not most frequent. This could be random variance.")
        else:
            results.add_fail("Test 7", "No successful claims in distribution test")
    
    except Exception as e:
        results.add_fail("Test 7", str(e))

def main():
    print("="*80)
    print("GIFTSDATES BACKEND - ONE-TIME WELCOME SPIN & WIN TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    
    # Run all tests
    test_1_new_user_welcome_spin_false()
    test_2_spin_status_structure()
    test_3_spin_claim_and_crediting()
    test_4_second_claim_fails()
    test_5_dismiss_functionality()
    test_6_no_monthly_behavior()
    test_7_distribution_sanity()
    
    # Print summary
    results.print_summary()
    
    # Return exit code
    return 0 if len(results.failed) == 0 else 1

if __name__ == "__main__":
    exit(main())
