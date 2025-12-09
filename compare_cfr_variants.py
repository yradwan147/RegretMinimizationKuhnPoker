"""
Comparison script for CFR, CFR+, NormalHedge, and NormalHedge+ algorithms.
Runs all four algorithms and compares convergence speed and final strategies.
"""
import numpy as np
import matplotlib.pyplot as plt
from kuhn_poker import GameConfig
from cfr import CFRTrainer
from cfr_plus import CFRPlusTrainer
from normal_hedge import NormalHedgeTrainer
from normal_hedge_plus import NormalHedgePlusTrainer
import time


def compare_algorithms(config: GameConfig, num_iterations: int = 10000):
    """
    Run CFR, CFR+, NormalHedge, and NormalHedge+ and compare their performance.
    
    Args:
        config: Game configuration
        num_iterations: Number of iterations for each algorithm
    """
    print("="*70)
    print("CFR vs CFR+ vs NormalHedge vs NormalHedge+ COMPARISON")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Ante: {config.ante}")
    print(f"  Bet size: {config.bet_size}")
    print(f"  Iterations: {num_iterations}")
    print()
    
    # Run vanilla CFR
    print("="*70)
    print("TRAINING VANILLA CFR")
    print("="*70)
    start_time = time.time()
    cfr_trainer = CFRTrainer(config)
    cfr_values = cfr_trainer.train(num_iterations)
    cfr_time = time.time() - start_time
    
    # Run CFR+ with different delay parameters
    cfr_plus_results = {}
    delays = [0, 100, 500]
    
    for delay in delays:
        print(f"\n{'='*70}")
        print(f"TRAINING CFR+ (delay={delay})")
        print("="*70)
        start_time = time.time()
        cfr_plus_trainer = CFRPlusTrainer(config, delay=delay)
        cfr_plus_values = cfr_plus_trainer.train(num_iterations)
        cfr_plus_time = time.time() - start_time
        
        cfr_plus_results[delay] = {
            'trainer': cfr_plus_trainer,
            'values': cfr_plus_values,
            'time': cfr_plus_time
        }
    
    # Run NormalHedge
    print(f"\n{'='*70}")
    print("TRAINING NORMALHEDGE")
    print("="*70)
    start_time = time.time()
    nh_trainer = NormalHedgeTrainer(config)
    nh_values = nh_trainer.train(num_iterations)
    nh_time = time.time() - start_time
    
    # Run NormalHedge+
    print(f"\n{'='*70}")
    print("TRAINING NORMALHEDGE+")
    print("="*70)
    start_time = time.time()
    nh_plus_trainer = NormalHedgePlusTrainer(config)
    nh_plus_values = nh_plus_trainer.train(num_iterations)
    nh_plus_time = time.time() - start_time
    
    # Calculate statistics
    print("\n" + "="*70)
    print("RESULTS COMPARISON")
    print("="*70)
    
    cfr_final = np.mean(cfr_values[-1000:])
    cfr_std = np.std(cfr_values[-1000:])
    
    print(f"\nVanilla CFR:")
    print(f"  Final value: {cfr_final:.6f} (±{cfr_std:.6f})")
    print(f"  Training time: {cfr_time:.2f}s")
    
    for delay in delays:
        result = cfr_plus_results[delay]
        final_value = np.mean(result['values'][-1000:])
        std_value = np.std(result['values'][-1000:])
        print(f"\nCFR+ (delay={delay}):")
        print(f"  Final value: {final_value:.6f} (±{std_value:.6f})")
        print(f"  Training time: {result['time']:.2f}s")
        print(f"  Speedup vs CFR: {cfr_time / result['time']:.2f}x")
    
    nh_final = np.mean(nh_values[-1000:])
    nh_std = np.std(nh_values[-1000:])
    print(f"\nNormalHedge:")
    print(f"  Final value: {nh_final:.6f} (±{nh_std:.6f})")
    print(f"  Training time: {nh_time:.2f}s")
    print(f"  Speedup vs CFR: {cfr_time / nh_time:.2f}x")
    
    nh_plus_final = np.mean(nh_plus_values[-1000:])
    nh_plus_std = np.std(nh_plus_values[-1000:])
    print(f"\nNormalHedge+:")
    print(f"  Final value: {nh_plus_final:.6f} (±{nh_plus_std:.6f})")
    print(f"  Training time: {nh_plus_time:.2f}s")
    print(f"  Speedup vs CFR: {cfr_time / nh_plus_time:.2f}x")
    print(f"  Speedup vs NormalHedge: {nh_time / nh_plus_time:.2f}x")
    
    # Plot comparison
    plot_comparison(cfr_values, cfr_plus_results, delays, nh_values, nh_plus_values, config)
    
    # Compare strategies
    print("\n" + "="*70)
    print("STRATEGY COMPARISON")
    print("="*70)
    compare_strategies(cfr_trainer, cfr_plus_results[0]['trainer'], nh_trainer, nh_plus_trainer)
    
    return cfr_trainer, cfr_plus_results, nh_trainer, nh_plus_trainer


def plot_comparison(cfr_values, cfr_plus_results, delays, nh_values, nh_plus_values, config):
    """
    Plot convergence comparison between CFR, CFR+, NormalHedge, and NormalHedge+.
    """
    iterations = range(1, len(cfr_values) + 1)
    
    # Calculate running averages
    def running_average(values):
        running_avg = []
        cumsum = 0
        for i, val in enumerate(values):
            cumsum += val
            running_avg.append(cumsum / (i + 1))
        return running_avg
    
    cfr_running_avg = running_average(cfr_values)
    nh_running_avg = running_average(nh_values)
    nh_plus_running_avg = running_average(nh_plus_values)
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Running averages
    ax1.plot(iterations, cfr_running_avg, label='Vanilla CFR', linewidth=2, color='blue')
    
    colors = ['red', 'green', 'orange']
    for i, delay in enumerate(delays):
        cfr_plus_running_avg = running_average(cfr_plus_results[delay]['values'])
        ax1.plot(iterations, cfr_plus_running_avg, 
                label=f'CFR+ (delay={delay})', linewidth=2, color=colors[i])
    
    # Add NormalHedge
    ax1.plot(iterations, nh_running_avg, label='NormalHedge', linewidth=2, 
             color='purple', linestyle='--')
    
    # Add NormalHedge+
    ax1.plot(iterations, nh_plus_running_avg, label='NormalHedge+', linewidth=2, 
             color='magenta', linestyle='-.')
    
    # Add Nash equilibrium reference
    nash_value = -1/18 if (config.ante == 1 and config.bet_size == 1) else None
    if nash_value is not None:
        ax1.axhline(y=nash_value, color='black', linestyle='--', 
                   label=f'Nash equilibrium', linewidth=2, alpha=0.5)
    
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Running Average Value')
    ax1.set_title('CFR vs CFR+ vs NormalHedge vs NormalHedge+: Convergence Comparison (Running Average)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Error from final value (convergence speed)
    # Use the best estimate as reference
    reference_value = np.mean(cfr_plus_results[delays[-1]]['values'][-2000:])
    
    def calculate_error(values, reference):
        return [abs(np.mean(values[:i+1]) - reference) for i in range(len(values))]
    
    cfr_error = calculate_error(cfr_values, reference_value)
    ax2.plot(iterations, cfr_error, label='Vanilla CFR', linewidth=2, color='blue')
    
    for i, delay in enumerate(delays):
        cfr_plus_error = calculate_error(cfr_plus_results[delay]['values'], reference_value)
        ax2.plot(iterations, cfr_plus_error, 
                label=f'CFR+ (delay={delay})', linewidth=2, color=colors[i])
    
    # Add NormalHedge error
    nh_error = calculate_error(nh_values, reference_value)
    ax2.plot(iterations, nh_error, label='NormalHedge', linewidth=2, 
             color='purple', linestyle='--')
    
    # Add NormalHedge+ error
    nh_plus_error = calculate_error(nh_plus_values, reference_value)
    ax2.plot(iterations, nh_plus_error, label='NormalHedge+', linewidth=2, 
             color='magenta', linestyle='-.')
    
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Absolute Error from Reference')
    ax2.set_title('Convergence Speed: Error from Final Estimate')
    ax2.set_yscale('log')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('cfr_vs_cfr_plus_vs_normalhedge_comparison.png', dpi=300, bbox_inches='tight')
    print(f"\nComparison plot saved to: cfr_vs_cfr_plus_vs_normalhedge_comparison.png")
    plt.show()


def compare_strategies(cfr_trainer, cfr_plus_trainer, nh_trainer, nh_plus_trainer):
    """
    Compare the learned strategies between CFR, CFR+, NormalHedge, and NormalHedge+.
    """
    cfr_profile = cfr_trainer.get_strategy_profile()
    cfr_plus_profile = cfr_plus_trainer.get_strategy_profile()
    nh_profile = nh_trainer.get_strategy_profile()
    nh_plus_profile = nh_plus_trainer.get_strategy_profile()
    
    # Compare key information sets
    key_info_sets = ['J', 'Q', 'K', 'Jb', 'Qb', 'Kb']
    
    print("\nKey Strategy Differences:")
    print("-" * 70)
    
    for info_set_key in key_info_sets:
        if (info_set_key in cfr_profile and info_set_key in cfr_plus_profile and 
            info_set_key in nh_profile and info_set_key in nh_plus_profile):
            print(f"\nInformation Set: {info_set_key}")
            
            cfr_strategy = cfr_profile[info_set_key]
            cfr_plus_strategy = cfr_plus_profile[info_set_key]
            nh_strategy = nh_profile[info_set_key]
            nh_plus_strategy = nh_plus_profile[info_set_key]
            
            # Calculate strategy differences
            actions = list(cfr_strategy.keys())
            max_diff_cfr_plus = 0
            max_diff_nh = 0
            max_diff_nh_plus = 0
            
            for action in actions:
                cfr_prob = cfr_strategy[action]
                cfr_plus_prob = cfr_plus_strategy.get(action, 0)
                nh_prob = nh_strategy.get(action, 0)
                nh_plus_prob = nh_plus_strategy.get(action, 0)
                diff_plus = abs(cfr_prob - cfr_plus_prob)
                diff_nh = abs(cfr_prob - nh_prob)
                diff_nh_plus = abs(cfr_prob - nh_plus_prob)
                max_diff_cfr_plus = max(max_diff_cfr_plus, diff_plus)
                max_diff_nh = max(max_diff_nh, diff_nh)
                max_diff_nh_plus = max(max_diff_nh_plus, diff_nh_plus)
                
                print(f"  {action:6s}: CFR={cfr_prob:.4f}, CFR+={cfr_plus_prob:.4f}, "
                      f"NH={nh_prob:.4f}, NH+={nh_plus_prob:.4f}")
                print(f"          Δ(CFR+)={diff_plus:.4f}, Δ(NH)={diff_nh:.4f}, Δ(NH+)={diff_nh_plus:.4f}")
            
            if max_diff_cfr_plus < 0.01 and max_diff_nh < 0.01 and max_diff_nh_plus < 0.01:
                print(f"  ✓ All strategies match closely")
            elif max_diff_cfr_plus < 0.05 and max_diff_nh < 0.05 and max_diff_nh_plus < 0.05:
                print(f"  ~ All strategies similar")
            else:
                print(f"  ⚠ Some significant differences")


def convergence_rate_analysis(config: GameConfig, iteration_counts: list):
    """
    Analyze convergence rate at different iteration counts.
    """
    print("\n" + "="*70)
    print("CONVERGENCE RATE ANALYSIS")
    print("="*70)
    
    cfr_errors = []
    cfr_plus_errors = []
    nh_errors = []
    nh_plus_errors = []
    reference_value = -1/18 if (config.ante == 1 and config.bet_size == 1) else None
    
    for num_iter in iteration_counts:
        print(f"\nTesting with {num_iter} iterations...")
        
        # CFR
        cfr_trainer = CFRTrainer(config)
        cfr_values = cfr_trainer.train(num_iter)
        cfr_final = np.mean(cfr_values[-max(100, num_iter//10):])
        
        # CFR+
        cfr_plus_trainer = CFRPlusTrainer(config, delay=0)
        cfr_plus_values = cfr_plus_trainer.train(num_iter)
        cfr_plus_final = np.mean(cfr_plus_values[-max(100, num_iter//10):])
        
        # NormalHedge
        nh_trainer = NormalHedgeTrainer(config)
        nh_values = nh_trainer.train(num_iter)
        nh_final = np.mean(nh_values[-max(100, num_iter//10):])
        
        # NormalHedge+
        nh_plus_trainer = NormalHedgePlusTrainer(config)
        nh_plus_values = nh_plus_trainer.train(num_iter)
        nh_plus_final = np.mean(nh_plus_values[-max(100, num_iter//10):])
        
        if reference_value is not None:
            cfr_error = abs(cfr_final - reference_value)
            cfr_plus_error = abs(cfr_plus_final - reference_value)
            nh_error = abs(nh_final - reference_value)
            nh_plus_error = abs(nh_plus_final - reference_value)
            cfr_errors.append(cfr_error)
            cfr_plus_errors.append(cfr_plus_error)
            nh_errors.append(nh_error)
            nh_plus_errors.append(nh_plus_error)
            
            print(f"  CFR:    {cfr_final:.6f}, error: {cfr_error:.6f}")
            print(f"  CFR+:   {cfr_plus_final:.6f}, error: {cfr_plus_error:.6f}")
            print(f"  NH:     {nh_final:.6f}, error: {nh_error:.6f}")
            print(f"  NH+:    {nh_plus_final:.6f}, error: {nh_plus_error:.6f}")
            print(f"  CFR+ improvement: {(cfr_error - cfr_plus_error) / cfr_error * 100:.1f}%")
            print(f"  NH improvement: {(cfr_error - nh_error) / cfr_error * 100:.1f}%")
            print(f"  NH+ improvement: {(cfr_error - nh_plus_error) / cfr_error * 100:.1f}%")
    
    # Plot convergence rate
    if reference_value is not None:
        plt.figure(figsize=(10, 6))
        plt.plot(iteration_counts, cfr_errors, 'o-', label='Vanilla CFR', 
                linewidth=2, markersize=8)
        plt.plot(iteration_counts, cfr_plus_errors, 's-', label='CFR+', 
                linewidth=2, markersize=8)
        plt.plot(iteration_counts, nh_errors, 'd-', label='NormalHedge', 
                linewidth=2, markersize=8)
        plt.plot(iteration_counts, nh_plus_errors, '^-', label='NormalHedge+', 
                linewidth=2, markersize=8)
        plt.xlabel('Number of Iterations')
        plt.ylabel('Error from Nash Equilibrium')
        plt.title('Convergence Rate: CFR vs CFR+ vs NormalHedge vs NormalHedge+')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig('convergence_rate_comparison.png', dpi=300, bbox_inches='tight')
        print(f"\nConvergence rate plot saved to: convergence_rate_comparison.png")
        plt.show()


def main():
    """
    Main function to run comprehensive CFR vs CFR+ vs NormalHedge vs NormalHedge+ comparison.
    """
    # Configuration
    config = GameConfig(ante=1, bet_size=1)
    
    # Main comparison
    cfr_trainer, cfr_plus_results, nh_trainer, nh_plus_trainer = compare_algorithms(config, num_iterations=10000)
    
    # Convergence rate analysis
    print("\n" + "="*70)
    print("Running convergence rate analysis...")
    print("="*70)
    convergence_rate_analysis(config, iteration_counts=[1000, 2000, 5000, 10000, 20000])
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - cfr_vs_cfr_plus_vs_normalhedge_comparison.png")
    print("  - convergence_rate_comparison.png")
    print("\n")


if __name__ == "__main__":
    main()



