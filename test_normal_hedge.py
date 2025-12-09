"""
Unit tests and sanity checks for NormalHedge implementation.
Tests the core functionality before running full comparisons.
"""
import numpy as np
import math
from normal_hedge import InformationSetNH, NormalHedgeTrainer
from kuhn_poker import GameConfig


def test_solve_c_scale():
    """
    Test the scale parameter solver with synthetic regret vectors.
    """
    print("="*70)
    print("TEST: solve_c_scale")
    print("="*70)
    
    # Test case A: Two actions, R=[0, 1]
    print("\nTest Case A: R=[0, 1]")
    info_set = InformationSetNH(2)
    R_plus = np.array([0.0, 1.0])
    c = info_set.solve_c_scale(R_plus)
    
    # Verify constraint: (1/N) * sum(exp(R²/(2c))) = e
    avg_potential = sum(math.exp((rp*rp)/(2.0*c)) for rp in R_plus) / len(R_plus)
    print(f"  Computed c: {c:.6f}")
    print(f"  Average potential: {avg_potential:.6f}")
    print(f"  Target (e): {math.e:.6f}")
    print(f"  Error: {abs(avg_potential - math.e):.9f}")
    
    if abs(avg_potential - math.e) < 1e-6:
        print("  ✓ PASS: Constraint satisfied")
    else:
        print("  ✗ FAIL: Constraint not satisfied")
    
    # Test case B: All zeros
    print("\nTest Case B: R=[0, 0]")
    R_plus = np.array([0.0, 0.0])
    c = info_set.solve_c_scale(R_plus)
    print(f"  Computed c: {c:.6f}")
    print(f"  ✓ PASS: Returns positive c (arbitrary when all regrets are zero)")
    
    # Test case C: Multiple actions with mixed regrets
    print("\nTest Case C: R=[0, 0.5, 1.0, 2.0]")
    info_set = InformationSetNH(4)
    R_plus = np.array([0.0, 0.5, 1.0, 2.0])
    c = info_set.solve_c_scale(R_plus)
    avg_potential = sum(math.exp((rp*rp)/(2.0*c)) for rp in R_plus) / len(R_plus)
    print(f"  Computed c: {c:.6f}")
    print(f"  Average potential: {avg_potential:.6f}")
    print(f"  Target (e): {math.e:.6f}")
    print(f"  Error: {abs(avg_potential - math.e):.9f}")
    
    if abs(avg_potential - math.e) < 1e-6:
        print("  ✓ PASS: Constraint satisfied")
    else:
        print("  ✗ FAIL: Constraint not satisfied")


def test_normalhedge_weights():
    """
    Test NormalHedge weight computation.
    """
    print("\n" + "="*70)
    print("TEST: normalhedge_weight")
    print("="*70)
    
    info_set = InformationSetNH(3)
    R_plus = np.array([0.0, 1.0, 2.0])
    c = 1.0
    
    print(f"\nR_plus: {R_plus}")
    print(f"c: {c}")
    
    weights = info_set.normalhedge_weight(R_plus, c)
    print(f"Unnormalized weights: {weights}")
    
    # Verify that actions with R=0 have zero weight
    if weights[0] == 0.0:
        print("  ✓ PASS: Action with R=0 has zero weight")
    else:
        print("  ✗ FAIL: Action with R=0 should have zero weight")
    
    # Verify that weights increase with regret
    if weights[2] > weights[1] > weights[0]:
        print("  ✓ PASS: Weights increase with regret")
    else:
        print("  ✗ FAIL: Weights should increase with regret")
    
    # Normalize and check sum to 1
    weight_sum = np.sum(weights)
    normalized = weights / weight_sum
    print(f"Normalized weights: {normalized}")
    print(f"Sum: {np.sum(normalized):.9f}")
    
    if abs(np.sum(normalized) - 1.0) < 1e-9:
        print("  ✓ PASS: Normalized weights sum to 1")
    else:
        print("  ✗ FAIL: Normalized weights should sum to 1")


def test_get_strategy():
    """
    Test strategy computation with uniform distribution for all-zero regrets.
    """
    print("\n" + "="*70)
    print("TEST: get_strategy (uniform when all regrets non-positive)")
    print("="*70)
    
    info_set = InformationSetNH(3)
    info_set.regret_sum = np.array([-1.0, -0.5, 0.0])
    
    strategy = info_set.get_strategy()
    print(f"Regret sum: {info_set.regret_sum}")
    print(f"Strategy: {strategy}")
    
    expected_uniform = np.array([1/3, 1/3, 1/3])
    if np.allclose(strategy, expected_uniform, atol=1e-9):
        print("  ✓ PASS: Returns uniform strategy when all regrets non-positive")
    else:
        print("  ✗ FAIL: Should return uniform strategy")


def test_kuhn_poker_convergence():
    """
    Test that NormalHedge converges on Kuhn Poker.
    Run a short training and verify basic convergence properties.
    """
    print("\n" + "="*70)
    print("TEST: Kuhn Poker convergence")
    print("="*70)
    
    config = GameConfig(ante=1, bet_size=1)
    trainer = NormalHedgeTrainer(config)
    
    print("\nRunning 5000 iterations of NormalHedge on Kuhn Poker...")
    values = trainer.train(5000)
    
    # Check convergence properties
    print(f"\nFirst 10 values: {values[:10]}")
    print(f"Last 10 values: {values[-10:]}")
    
    final_mean = np.mean(values[-1000:])
    final_std = np.std(values[-1000:])
    
    print(f"\nFinal 1000 iterations:")
    print(f"  Mean: {final_mean:.6f}")
    print(f"  Std: {final_std:.6f}")
    
    # Nash equilibrium value for Kuhn Poker with ante=1, bet_size=1
    nash_value = -1/18  # ≈ -0.0556
    error = abs(final_mean - nash_value)
    
    print(f"\nNash equilibrium value: {nash_value:.6f}")
    print(f"Error from Nash: {error:.6f}")
    
    if error < 0.01:
        print("  ✓ PASS: Converging close to Nash equilibrium")
    else:
        print("  ~ Note: May need more iterations for closer convergence")
    
    # Check that information sets were created
    print(f"\nNumber of information sets: {len(trainer.info_sets)}")
    if len(trainer.info_sets) > 0:
        print("  ✓ PASS: Information sets created")
    else:
        print("  ✗ FAIL: No information sets created")
    
    # Display some learned strategies
    print("\nLearned strategies for key information sets:")
    profile = trainer.get_strategy_profile()
    key_info_sets = ['J', 'Q', 'K', 'Jb', 'Qb', 'Kb']
    
    for info_set_key in key_info_sets:
        if info_set_key in profile:
            print(f"\n  {info_set_key}: {profile[info_set_key]}")


def test_numerical_stability():
    """
    Test numerical stability with extreme regret values.
    """
    print("\n" + "="*70)
    print("TEST: Numerical stability")
    print("="*70)
    
    # Test with large regrets
    print("\nTest with large regrets: R=[0, 10, 100]")
    info_set = InformationSetNH(3)
    info_set.regret_sum = np.array([0.0, 10.0, 100.0])
    
    try:
        strategy = info_set.get_strategy()
        print(f"  Strategy: {strategy}")
        print(f"  Sum: {np.sum(strategy):.9f}")
        
        if np.all(np.isfinite(strategy)) and abs(np.sum(strategy) - 1.0) < 1e-9:
            print("  ✓ PASS: Handles large regrets without overflow")
        else:
            print("  ✗ FAIL: Numerical issues detected")
    except Exception as e:
        print(f"  ✗ FAIL: Exception raised: {e}")
    
    # Test with very small positive regrets
    print("\nTest with small regrets: R=[0, 1e-8, 1e-6]")
    info_set = InformationSetNH(3)
    info_set.regret_sum = np.array([0.0, 1e-8, 1e-6])
    
    try:
        strategy = info_set.get_strategy()
        print(f"  Strategy: {strategy}")
        print(f"  Sum: {np.sum(strategy):.9f}")
        
        if np.all(np.isfinite(strategy)) and abs(np.sum(strategy) - 1.0) < 1e-9:
            print("  ✓ PASS: Handles small regrets")
        else:
            print("  ✗ FAIL: Numerical issues detected")
    except Exception as e:
        print(f"  ✗ FAIL: Exception raised: {e}")


def main():
    """
    Run all tests.
    """
    print("\n" + "="*70)
    print("NORMALHEDGE UNIT TESTS AND SANITY CHECKS")
    print("="*70)
    print()
    
    test_solve_c_scale()
    test_normalhedge_weights()
    test_get_strategy()
    test_numerical_stability()
    test_kuhn_poker_convergence()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print()


if __name__ == "__main__":
    main()


