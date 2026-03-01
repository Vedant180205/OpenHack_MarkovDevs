import requests
import time
import sys

BASE_URL = "http://localhost:8000"

TEST_CASES = [
    {
        "name": "Exemption Applied (Trade Secrets)",
        "prompt": "A consumer submitted a verifiable request to know the specific pieces of data we collected. We provided their data, but refused to disclose the proprietary algorithm and trade secrets we used to calculate their internal user score.",
        "expect_harmful": False
        # Safe under Section 1798.100(f) (Trade Secret Exemption)
    },
    {
        "name": "Sensitive Data Violation (Biometrics)",
        "prompt": "Our physical gym locations collect fingerprint scans to uniquely identify members for entry. We do not provide any 'Limit the Use of My Sensitive Personal Information' notices or links.",
        "expect_harmful": True
        # Should flag Section 1798.121 or 1798.135
    },
    {
        "name": "Exemption Applied (Educational Assessment)",
        "prompt": "A high school student requested that we delete their SAT scores and standardized test responses that we process and hold on behalf of their school district. We denied the deletion request.",
        "expect_harmful": False
        # Safe under Section 1798.145(q) (Educational Assessment Exemption)
    },
    {
        "name": "Clear Violation (Dark Patterns)",
        "prompt": "We provide a 'Do Not Sell My Personal Information' link, but clicking it opens a confusing popup with inverted colors, a 30-second unskippable countdown timer, and language that implies their account will be deleted if they proceed.",
        "expect_harmful": True
        # Should flag Section 1798.135 (Opt-out procedures / Dark Patterns)
    },
    {
        "name": "Clear Violation (Right to Know Sources)",
        "prompt": "A consumer submitted a verifiable request asking for the categories of sources from which we collected their personal information. We told them we only have to disclose the data itself, not where we bought it from.",
        "expect_harmful": True
        # Should flag Section 1798.110 (Right to Know Categories of Sources)
    }
]

def check_health():
    print("⏳ Waiting for API to become ready (Checking /health)...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200 and response.json().get("status") == "ready":
                print("✅ API is healthy and ready!\n")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        time.sleep(2)
        sys.stdout.write(".")
        sys.stdout.flush()
        
    print("\n❌ API Health Check Failed. Did you start the server?")
    return False

def test_analyze_endpoint():
    passed = 0
    total = len(TEST_CASES)
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"--- Test {i}/{total}: {test['name']} ---")
        payload = {"prompt": test["prompt"]}
        
        try:
            # The judges usually set a 30-60 second timeout for LLM generation
            response = requests.post(f"{BASE_URL}/analyze", json=payload, timeout=300)
            
            if response.status_code != 200:
                print(f"❌ FAIL: API returned status code {response.status_code}")
                print(response.text)
                continue
                
            data = response.json()
            print(f"Output: {data}")
            
            # 1. Format Validation (The most important part)
            if "harmful" not in data or "articles" not in data:
                print("❌ FAIL: Missing required JSON keys ('harmful' or 'articles').")
                continue
                
            if not isinstance(data["harmful"], bool):
                print("❌ FAIL: 'harmful' must be a boolean.")
                continue
                
            if not isinstance(data["articles"], list):
                print("❌ FAIL: 'articles' must be a list.")
                continue
                
            # 2. Logic Validation
            if data["harmful"] is False and len(data["articles"]) > 0:
                print("❌ FAIL: 'articles' list must be EMPTY when harmful is False.")
                continue
                
            print("✅ PASS: Format is perfectly valid.")
            passed += 1
            
        except requests.exceptions.Timeout:
            print("❌ FAIL: Request timed out. The LLM took too long.")
        except Exception as e:
            print(f"❌ FAIL: Unexpected error: {e}")
            
        print("")

    print("========================================")
    print(f"🏁 Final Score: {passed}/{total} Format Tests Passed")
    if passed == total:
        print("🏆 YOUR API IS READY FOR SUBMISSION!")
    else:
        print("⚠️ Fix the errors before building Docker.")

if __name__ == "__main__":
    if check_health():
        test_analyze_endpoint()