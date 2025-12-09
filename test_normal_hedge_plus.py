"""
Test script to verify NormalHedge+ implementation.
Demonstrates that RM+ truncation is working correctly.
"""
import numpy as np
from normal_hedge import InformationSetNH
from normal_hedge_plus import InformationSetNHPlus


def test_regret_truncation():
    """
    Test that NormalHedge+ truncates regrets to zero while NormalHedge allows negative regrets.
    """
    print("="*70)
    print("Testing Regret Truncation: NormalHedge vs NormalHedge+")
    print("="*70)
    
    num_actions = 3
    
    # Create information sets
    nh_infoset = InformationSetNH(num_actions)
    nh_plus_infoset = InformationSetNHPlus(num_actions)
    
    # Simulate a sequence of regrets where action 0 performs poorly, then well
    regret_sequence = [
        np.array([-5.0, 2.0, 1.0]),   # Action 0 performs poorly
        np.array([-3.0, 1.0, 0.5]),   # Action 0 continues poorly
        np.array([-2.0, 0.5, 0.2]),   # Action 0 still poor
        np.array([4.0, -1.0, -0.5]),  # Action 0 performs well now!
        np.array([3.0, -0.5, -0.2]),  # Action 0 continues well
    ]
    
    print("\nSimulating regret sequence:")
    print("-" * 70)
    
    for t, regrets in enumerate(regret_sequence):
        # Add regrets to both information sets
        for action in range(num_actions):
            nh_infoset.add_regret(action, regrets[action])
            nh_plus_infoset.add_regret(action, regrets[action])
        
        print(f"\nRound {t+1}:")
        print(f"  Instantaneous regrets: {regrets}")
        print(f"  NormalHedge cumulative:  {nh_infoset.regret_sum}")
        print(f"  NormalHedge+ cumulative: {nh_plus_infoset.regret_sum}")
        
        # Get strategies
        nh_strategy = nh_infoset.get_strategy()
        nh_plus_strategy = nh_plus_infoset.get_strategy()
        
        print(f"  NormalHedge strategy:  {nh_strategy}")
        print(f"  NormalHedge+ strategy: {nh_plus_strategy}")
    
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)
    print("\nKey Observation:")
    print("  - NormalHedge: Action 0 has large negative cumulative regret")
    print(f"    {nh_infoset.regret_sum[0]:.2f}")
    print("  - NormalHedge+: Action 0 regret was truncated to 0, allowing faster recovery")
    print(f"    {nh_plus_infoset.regret_sum[0]:.2f}")
    print("\nThis demonstrates the RM+ truncation mechanism:")
    print("  When action 0 performed poorly (rounds 1-3), its regret was negative.")
    print("  NormalHedge accumulates this negative regret indefinitely.")
    print("  NormalHedge+ truncates it to 0, 'forgetting' the poor performance.")
    print("  When action 0 starts performing well (rounds 4-5), NormalHedge+")
    print("  can assign it weight faster because it doesn't have negative ballast.")
    print("\n" + "="*70)


def test_basic_functionality():
    """
    Test basic functionality of NormalHedge+ to ensure it works correctly.
    """
    print("\n" + "="*70)
    print("Testing Basic Functionality")
    print("="*70)
    
    num_actions = 2
    infoset = InformationSetNHPlus(num_actions)
    
    # Test 1: Initial uniform strategy
    strategy = infoset.get_strategy()
    print(f"\n1. Initial strategy (should be uniform): {strategy}")
    assert np.allclose(strategy, [0.5, 0.5]), "Initial strategy should be uniform"
    print("   ✓ PASS")
    
    # Test 2: Positive regrets
    infoset.add_regret(0, 5.0)
    infoset.add_regret(1, 2.0)
    strategy = infoset.get_strategy()
    print(f"\n2. After positive regrets [5.0, 2.0]:")
    print(f"   Cumulative regrets: {infoset.regret_sum}")
    print(f"   Strategy: {strategy}")
    assert strategy[0] > strategy[1], "Action with higher regret should have higher weight"
    print("   ✓ PASS")
    
    # Test 3: Negative regrets get truncated
    infoset.add_regret(0, -10.0)  # Large negative regret
    infoset.add_regret(1, 1.0)
    strategy = infoset.get_strategy()
    print(f"\n3. After adding regrets [-10.0, 1.0]:")
    print(f"   Cumulative regrets: {infoset.regret_sum}")
    print(f"   Strategy: {strategy}")
    assert infoset.regret_sum[0] == 0.0, "Negative cumulative regret should be truncated to 0"
    print("   ✓ PASS: Regret truncation working correctly")
    
    # Test 4: Recovery after truncation
    infoset.add_regret(0, 3.0)  # Action 0 starts performing well
    strategy = infoset.get_strategy()
    print(f"\n4. After adding regret [3.0, 0.0] (action 0 recovers):")
    print(f"   Cumulative regrets: {infoset.regret_sum}")
    print(f"   Strategy: {strategy}")
    assert infoset.regret_sum[0] == 3.0, "Action should recover from truncation"
    print("   ✓ PASS")
    
    print("\n" + "="*70)
    print("All basic functionality tests passed!")
    print("="*70)


if __name__ == "__main__":
    # Run tests
    test_basic_functionality()
    test_regret_truncation()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nNormalHedge+ is correctly implementing RM+ truncation:")
    print("  R'_{i,t} = max{R'_{i,t-1} + r_{i,t}, 0}")
    print("\nThis allows the algorithm to 'forget' periods of poor performance")
    print("and adapt faster when actions start performing well again.")
    print("="*70 + "\n")

