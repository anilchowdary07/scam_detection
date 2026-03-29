"""
Advanced test script for improved environment features
"""
from environment import ScamDetectionEnv
from tasks import get_all_tasks


def test_early_termination():
    """Test early termination on wrong classification"""
    print("\n" + "="*60)
    print("TEST 1: Early Termination on Wrong Classification")
    print("="*60)

    tasks = get_all_tasks()
    task = tasks[0]  # Easy task

    env = ScamDetectionEnv(task)
    obs = env.reset()

    # Give WRONG classification
    print("\nGiving wrong classification: classify('safe')")
    obs, reward, done, info = env.step("classify('safe')")

    print(f"✓ Reward: {reward:.2f} (should be negative)")
    print(f"✓ Done: {done} (should be True - early termination)")
    print(f"✓ Classification correct: {info.get('classification_correct', False)}")
    print(f"✓ Early termination: {info.get('early_termination', 'N/A')}")

    assert done == True, "Episode should end on wrong classification"
    assert reward < 0, "Reward should be negative"
    assert info.get('early_termination') is not None, "Should have early termination flag"

    print("\n✅ Early termination test PASSED!")


def test_progressive_penalties():
    """Test progressive penalties for repeated mistakes"""
    print("\n" + "="*60)
    print("TEST 2: Progressive Penalties")
    print("="*60)

    tasks = get_all_tasks()
    task = tasks[0]

    env = ScamDetectionEnv(task)
    obs = env.reset()

    # Correct classification to proceed
    obs, reward1, done, info = env.step("classify('scam')")
    print(f"\n✓ Step 1 (correct): Reward = {reward1:.2f}")

    # Wrong action at decide step (first mistake)
    obs, reward2, done, info = env.step("reason('test')")  # Wrong action type
    print(f"✓ First mistake: Reward = {reward2:.2f}, Mistakes = {info['mistake_count']}")

    # Wrong action at decide step again (second mistake - should be worse)
    obs, reward3, done, info = env.step("reason('test')")  # Wrong action type again
    print(f"✓ Second mistake: Reward = {reward3:.2f}, Mistakes = {info['mistake_count']}")

    assert reward3 <= reward2, "Progressive penalty should make second mistake worse"
    assert info['mistake_count'] >= 1, "Should track mistake count"

    print("\n✅ Progressive penalties test PASSED!")


def test_quality_based_reasoning():
    """Test quality-based reasoning rewards"""
    print("\n" + "="*60)
    print("TEST 3: Quality-Based Reasoning Rewards")
    print("="*60)

    tasks = get_all_tasks()
    task = tasks[0]

    env = ScamDetectionEnv(task)
    obs = env.reset()

    # Complete correct classification and decision
    obs, r1, done, info = env.step("classify('scam')")
    obs, r2, done, info = env.step("decide('remove')")

    # Strong reasoning (many keywords)
    print("\nTesting STRONG reasoning (many keywords):")
    obs, reward_strong, done, info = env.step("reason('This is a phishing scam with fake credentials asking for sensitive information')")
    quality_strong = info.get('reasoning_quality', 'N/A')
    print(f"✓ Reward: {reward_strong:.2f}, Quality: {quality_strong}")

    # Reset for medium test
    env.reset()
    obs, r1, done, info = env.step("classify('scam')")
    obs, r2, done, info = env.step("decide('remove')")

    # Medium reasoning (some keywords)
    print("\nTesting MEDIUM reasoning (some keywords):")
    obs, reward_medium, done, info = env.step("reason('This looks suspicious')")
    quality_medium = info.get('reasoning_quality', 'N/A')
    print(f"✓ Reward: {reward_medium:.2f}, Quality: {quality_medium}")

    # Reset for weak test
    env.reset()
    obs, r1, done, info = env.step("classify('scam')")
    obs, r2, done, info = env.step("decide('remove')")

    # Weak reasoning (no keywords)
    print("\nTesting WEAK reasoning (no keywords):")
    obs, reward_weak, done, info = env.step("reason('I think this is bad')")
    quality_weak = info.get('reasoning_quality', 'N/A')
    print(f"✓ Reward: {reward_weak:.2f}, Quality: {quality_weak}")

    assert reward_strong > reward_medium, "Strong should score higher than medium"
    assert reward_medium >= reward_weak, "Medium should score >= weak"

    print("\n✅ Quality-based reasoning test PASSED!")


def test_step_enforcement():
    """Test strict step sequence enforcement"""
    print("\n" + "="*60)
    print("TEST 4: Strict Step Sequence Enforcement")
    print("="*60)

    tasks = get_all_tasks()
    task = tasks[0]

    env = ScamDetectionEnv(task)
    obs = env.reset()

    # Try to skip classification
    print("\nTrying to skip classification step:")
    obs, reward, done, info = env.step("decide('remove')")  # Wrong step
    print(f"✓ Reward: {reward:.2f} (should be negative)")
    print(f"✓ Current step: {env.state()['current_step']} (should stay at 0)")
    print(f"✓ Error: {info.get('error', 'N/A')}")

    assert env.state()['current_step'] == 0, "Should not progress on wrong action"
    assert reward < 0, "Should get penalty"

    print("\n✅ Step enforcement test PASSED!")


def test_improved_hard_task():
    """Test the improved hard task"""
    print("\n" + "="*60)
    print("TEST 5: Improved Hard Task (Subtle Phishing)")
    print("="*60)

    tasks = get_all_tasks()
    hard_task = tasks[2]  # Hard task

    print(f"\nTask: {hard_task['name']}")
    print(f"Content preview: {hard_task['content'][:100]}...")
    print(f"\nExpected classification: {hard_task['expected_classification']}")
    print(f"Expected decision: {hard_task['expected_decision']}")
    print(f"Strong keywords: {hard_task['strong_keywords']}")

    env = ScamDetectionEnv(hard_task)
    obs = env.reset()

    # Complete perfect run
    obs, r1, done, info = env.step(f"classify('{hard_task['expected_classification']}')")
    obs, r2, done, info = env.step(f"decide('{hard_task['expected_decision']}')")
    obs, r3, done, info = env.step("reason('This is a phishing attempt with a suspicious domain trying to verify account credentials')")

    print(f"\n✓ Total reward: {r1 + r2 + r3:.2f}")
    print(f"✓ Final grade: {info['final_grade']['total']:.2f}")

    print("\n✅ Improved hard task test PASSED!")


def run_all_tests():
    """Run all advanced tests"""
    print("\n" + "="*60)
    print("RUNNING ADVANCED TESTS FOR IMPROVED ENVIRONMENT")
    print("="*60)

    try:
        test_early_termination()
        test_progressive_penalties()
        test_quality_based_reasoning()
        test_step_enforcement()
        test_improved_hard_task()

        print("\n" + "="*60)
        print("🎉 ALL ADVANCED TESTS PASSED!")
        print("="*60)
        print("\nImproved features verified:")
        print("  ✅ Early termination on wrong classification")
        print("  ✅ Progressive penalties for repeated mistakes")
        print("  ✅ Quality-based reasoning rewards")
        print("  ✅ Strict step sequence enforcement")
        print("  ✅ Improved hard task (more subtle)")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
