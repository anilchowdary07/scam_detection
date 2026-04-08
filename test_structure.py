#!/usr/bin/env python3
"""
Quick structure validation test (without running the server)
"""
import sys
import os

def test_files_exist():
    """Check all required files exist"""
    required_files = [
        "app.py",
        "environment.py",
        "models.py",
        "inference.py",
        "Dockerfile",
        "requirements.txt",
        "pyproject.toml",
        "openenv.yaml",
        "README.md",
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    print("✅ All required files present")
    return True

def test_pyproject_toml():
    """Check pyproject.toml has required sections"""
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
        
        required = ["[project]", "[build-system]", "[tool.openenv]"]
        missing = [r for r in required if r not in content]
        
        if missing:
            print(f"❌ Missing sections in pyproject.toml: {missing}")
            return False
        
        print("✅ pyproject.toml has all required sections")
        return True
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return False

def test_app_structure():
    """Check app.py has FastAPI endpoints"""
    try:
        with open("app.py", "r") as f:
            content = f.read()
        
        required_endpoints = [
            'app = FastAPI',
            '@app.get("/")',
            '@app.post("/reset"',
            '@app.post("/step"',
            '@app.get("/state"'
        ]
        
        missing = [e for e in required_endpoints if e not in content]
        
        if missing:
            print(f"❌ Missing in app.py: {missing}")
            return False
        
        print("✅ app.py has all required FastAPI endpoints")
        return True
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def main():
    print("=" * 60)
    print("OpenEnv Structure Validation")
    print("=" * 60)
    
    tests = [
        test_files_exist,
        test_pyproject_toml,
        test_app_structure,
    ]
    
    results = [test() for test in tests]
    
    print("=" * 60)
    if all(results):
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
