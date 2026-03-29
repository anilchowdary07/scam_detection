"""
Test script to verify the environment works correctly
"""
from environment import ScamDetectionEnv
from tasks import get_all_tasks


def test_environment():
    """Test basic environment functionality"""
    print("Testing Scam Detection Environment...\n")

    # Get a task
    tasks = get_all_tasks()
    task = tasks[0]  # Easy task

    print(f"1. Testing with task: {task['name']}")

    # Create environment
    env = ScamDetectionEnv(task)

    # Test reset
    obs = env.reset()
    print(f"✓ Reset successful")
    print(f"  Initial step type: {obs.step_type}")
    assert obs.step_type == "classify", "Initial step should be classify"

    # Test step 1 - classify
    obs, reward, done, info = env.step("classify('scam')")
    print(f"✓ Step 1 (classify) executed")
    print(f"  Reward: {reward}")
    print(f"  Done: {done}")
    assert not done, "Should not be done after step 1"
    assert obs.step_type == "decide", "Next step should be decide"
    assert isinstance(reward, float), "Reward must be float"

    # Test step 2 - decide
    obs, reward, done, info = env.step("decide('remove')")
    print(f"✓ Step 2 (decide) executed")
    print(f"  Reward: {reward}")
    print(f"  Done: {done}")
    assert not done, "Should not be done after step 2"
    assert obs.step_type == "reason", "Next step should be reason"
    assert isinstance(reward, float), "Reward must be float"

    # Test step 3 - reason
    obs, reward, done, info = env.step("reason('This is a phishing scam asking for credentials')")
    print(f"✓ Step 3 (reason) executed")
    print(f"  Reward: {reward}")
    print(f"  Done: {done}")
    assert done, "Should be done after step 3"
    assert isinstance(reward, float), "Reward must be float"

    # Check final grade
    assert 'final_grade' in info, "Final grade should be in info"
    final_grade = info['final_grade']
    print(f"\n2. Final Grade:")
    print(f"  Total: {final_grade['total']:.2f}")
    print(f"  Classification: {final_grade['classification']:.2f}")
    print(f"  Decision: {final_grade['decision']:.2f}")
    print(f"  Reasoning: {final_grade['reasoning']:.2f}")

    # Verify scores are in 0.0-1.0 range
    assert 0.0 <= final_grade['total'] <= 1.0, "Total score must be 0.0-1.0"
    assert 0.0 <= final_grade['classification'] <= 1.0, "Classification score must be 0.0-1.0"
    assert 0.0 <= final_grade['decision'] <= 1.0, "Decision score must be 0.0-1.0"
    assert 0.0 <= final_grade['reasoning'] <= 1.0, "Reasoning score must be 0.0-1.0"

    # Test state
    state = env.state()
    print(f"\n3. Final State:")
    print(f"  Classification: {state['classification']}")
    print(f"  Decision: {state['decision']}")
    print(f"  Reasoning: {state['reasoning']}")

    print(f"\n✅ All tests passed!")


if __name__ == "__main__":
    test_environment()
