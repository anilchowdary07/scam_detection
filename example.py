"""
Example script showing manual interaction with the environment (no LLM)
"""
from environment import ScamDetectionEnv
from tasks import get_all_tasks


def run_manual_example():
    """Run example with hardcoded actions"""
    print("=== Manual Environment Example ===\n")

    # Get all tasks
    tasks = get_all_tasks()

    for task in tasks:
        print(f"\n{'='*60}")
        print(f"Task: {task['name']} ({task['difficulty']})")
        print(f"{'='*60}")
        print(f"\nContent:\n{task['content']}\n")

        # Create environment
        env = ScamDetectionEnv(task)

        # Reset
        obs = env.reset()
        print(f"Step 1 - {obs.message}")

        # Step 1: Classify
        action1 = f"classify('{task['expected_classification']}')"
        print(f"Action: {action1}")
        obs, reward, done, info = env.step(action1)
        print(f"Reward: {reward:.2f}\n")

        # Step 2: Decide
        print(f"Step 2 - {obs.message}")
        action2 = f"decide('{task['expected_decision']}')"
        print(f"Action: {action2}")
        obs, reward, done, info = env.step(action2)
        print(f"Reward: {reward:.2f}\n")

        # Step 3: Reason
        print(f"Step 3 - {obs.message}")
        reasoning = f"This appears to be a {task['expected_classification']} with indicators including {', '.join(task['expected_reasoning_keywords'][:3])}"
        action3 = f"reason('{reasoning}')"
        print(f"Action: {action3}")
        obs, reward, done, info = env.step(action3)
        print(f"Reward: {reward:.2f}\n")

        # Show final grade
        if 'final_grade' in info:
            grade = info['final_grade']
            print(f"{'='*60}")
            print("FINAL GRADE")
            print(f"{'='*60}")
            print(f"Total Score: {grade['total']:.2f}")
            print(f"  - Classification: {grade['classification']:.2f} (weight: {grade['classification_weight']})")
            print(f"  - Decision: {grade['decision']:.2f} (weight: {grade['decision_weight']})")
            print(f"  - Reasoning: {grade['reasoning']:.2f} (weight: {grade['reasoning_weight']})")


if __name__ == "__main__":
    run_manual_example()
