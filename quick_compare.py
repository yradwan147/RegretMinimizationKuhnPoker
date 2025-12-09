"""
Quick comparison of CFR, CFR+, NormalHedge, and NormalHedge+ with fewer iterations.
This is a faster version for testing before running the full comparison.
"""
import numpy as np
import matplotlib.pyplot as plt
from kuhn_poker import GameConfig
from cfr import CFRTrainer
from cfr_plus import CFRPlusTrainer
from normal_hedge import NormalHedgeTrainer
from normal_hedge_plus import NormalHedgePlusTrainer
import time


def quick_compare(num_iterations=2000):
    """
    Quick comparison of all four algorithms.
    """
    config = GameConfig(ante=1, bet_size=1)
    nash_value = -1/18  # Nash equilibrium for standard Kuhn Poker
    
    print("="*70)
    print("QUICK COMPARISON: CFR vs CFR+ vs NormalHedge vs NormalHedge+")
    print("="*70)
    print(f"\nIterations: {num_iterations}")
    print(f"Nash equilibrium value: {nash_value:.6f}\n")
    
    # Run CFR
    print("Training CFR...")
    start = time.time()
    cfr_trainer = CFRTrainer(config)
    cfr_values = cfr_trainer.train(num_iterations)
    cfr_time = time.time() - start
    cfr_final = np.mean(cfr_values[-200:])
    cfr_error = abs(cfr_final - nash_value)
    
    # Run CFR+
    print("Training CFR+...")
    start = time.time()
    cfr_plus_trainer = CFRPlusTrainer(config, delay=0)
    cfr_plus_values = cfr_plus_trainer.train(num_iterations)
    cfr_plus_time = time.time() - start
    cfr_plus_final = np.mean(cfr_plus_values[-200:])
    cfr_plus_error = abs(cfr_plus_final - nash_value)
    
    # Run NormalHedge
    print("Training NormalHedge...")
    start = time.time()
    nh_trainer = NormalHedgeTrainer(config)
    nh_values = nh_trainer.train(num_iterations)
    nh_time = time.time() - start
    nh_final = np.mean(nh_values[-200:])
    nh_error = abs(nh_final - nash_value)
    
    # Run NormalHedge+
    print("Training NormalHedge+...")
    start = time.time()
    nh_plus_trainer = NormalHedgePlusTrainer(config)
    nh_plus_values = nh_plus_trainer.train(num_iterations)
    nh_plus_time = time.time() - start
    nh_plus_final = np.mean(nh_plus_values[-200:])
    nh_plus_error = abs(nh_plus_final - nash_value)
    
    # Print results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nCFR:")
    print(f"  Final value: {cfr_final:.6f}")
    print(f"  Error from Nash: {cfr_error:.6f}")
    print(f"  Time: {cfr_time:.2f}s")
    
    print(f"\nCFR+:")
    print(f"  Final value: {cfr_plus_final:.6f}")
    print(f"  Error from Nash: {cfr_plus_error:.6f}")
    print(f"  Time: {cfr_plus_time:.2f}s")
    print(f"  Improvement over CFR: {(1 - cfr_plus_error/cfr_error)*100:.1f}%")
    
    print(f"\nNormalHedge:")
    print(f"  Final value: {nh_final:.6f}")
    print(f"  Error from Nash: {nh_error:.6f}")
    print(f"  Time: {nh_time:.2f}s")
    print(f"  Improvement over CFR: {(1 - nh_error/cfr_error)*100:.1f}%")
    
    print(f"\nNormalHedge+:")
    print(f"  Final value: {nh_plus_final:.6f}")
    print(f"  Error from Nash: {nh_plus_error:.6f}")
    print(f"  Time: {nh_plus_time:.2f}s")
    print(f"  Improvement over CFR: {(1 - nh_plus_error/cfr_error)*100:.1f}%")
    print(f"  Improvement over NormalHedge: {(1 - nh_plus_error/nh_error)*100:.1f}%")
    
    # Plot convergence
    plt.figure(figsize=(12, 6))
    
    iterations = range(1, num_iterations + 1)
    
    # Running averages
    def running_avg(vals):
        return [np.mean(vals[:i+1]) for i in range(len(vals))]
    
    plt.plot(iterations, running_avg(cfr_values), label='CFR', linewidth=2)
    plt.plot(iterations, running_avg(cfr_plus_values), label='CFR+', linewidth=2)
    plt.plot(iterations, running_avg(nh_values), label='NormalHedge', linewidth=2)
    plt.plot(iterations, running_avg(nh_plus_values), label='NormalHedge+', linewidth=2)
    plt.axhline(y=nash_value, color='black', linestyle='--', 
                label='Nash Equilibrium', alpha=0.5)
    
    plt.xlabel('Iteration')
    plt.ylabel('Running Average Value')
    plt.title('Quick Comparison: CFR vs CFR+ vs NormalHedge vs NormalHedge+')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('quick_comparison.png', dpi=300, bbox_inches='tight')
    print("\n✓ Plot saved to: quick_comparison.png")
    
    # Compare key strategies
    print("\n" + "="*70)
    print("KEY STRATEGY COMPARISON")
    print("="*70)
    
    cfr_profile = cfr_trainer.get_strategy_profile()
    cfr_plus_profile = cfr_plus_trainer.get_strategy_profile()
    nh_profile = nh_trainer.get_strategy_profile()
    nh_plus_profile = nh_plus_trainer.get_strategy_profile()
    
    key_info_sets = ['J', 'K', 'Kb']
    
    for info_set in key_info_sets:
        if info_set in cfr_profile:
            print(f"\n{info_set}:")
            print(f"  CFR:     {cfr_profile[info_set]}")
            print(f"  CFR+:    {cfr_plus_profile.get(info_set, {})}")
            print(f"  NH:      {nh_profile.get(info_set, {})}")
            print(f"  NH+:     {nh_plus_profile.get(info_set, {})}")
    
    print("\n" + "="*70)
    print("✓ COMPARISON COMPLETE")
    print("="*70)


if __name__ == "__main__":
    quick_compare(2000)


