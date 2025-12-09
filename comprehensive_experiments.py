"""
Comprehensive Experiments for Algorithm Comparison Report
Tests CFR, CFR+, NormalHedge, and NormalHedge+ under various configurations.
Generates comparison plots for visualization.
"""
import numpy as np
import matplotlib.pyplot as plt
import time
from kuhn_poker import GameConfig
from cfr import CFRTrainer
from cfr_plus import CFRPlusTrainer
from normal_hedge import NormalHedgeTrainer
from normal_hedge_plus import NormalHedgePlusTrainer

# Suppress iteration printing for cleaner output
import sys
from io import StringIO

# Algorithm colors and styles for consistent plotting
ALG_COLORS = {
    'CFR': 'blue',
    'CFR+': 'red',
    'NormalHedge': 'purple',
    'NormalHedge+': 'magenta'
}
ALG_STYLES = {
    'CFR': '-',
    'CFR+': '-',
    'NormalHedge': '--',
    'NormalHedge+': '-.'
}
ALG_MARKERS = {
    'CFR': 'o',
    'CFR+': 's',
    'NormalHedge': 'd',
    'NormalHedge+': '^'
}


def run_silent(trainer_class, config, num_iterations, **kwargs):
    """Run training silently (without print statements)."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    trainer = trainer_class(config, **kwargs) if kwargs else trainer_class(config)
    start_time = time.time()
    values = trainer.train(num_iterations)
    elapsed_time = time.time() - start_time
    
    sys.stdout = old_stdout
    return trainer, values, elapsed_time


def compute_metrics(values, nash_value):
    """Compute convergence metrics."""
    # Use last 10% of iterations for final estimate
    tail_size = max(100, len(values) // 10)
    final_value = np.mean(values[-tail_size:])
    final_std = np.std(values[-tail_size:])
    error = abs(final_value - nash_value)
    
    # Running average for convergence
    running_avg = np.cumsum(values) / np.arange(1, len(values) + 1)
    
    return {
        'final_value': final_value,
        'final_std': final_std,
        'error': error,
        'running_avg': running_avg
    }


def run_experiment(config_name, config, num_iterations, nash_value):
    """Run all four algorithms and collect results."""
    print(f"\n{'='*70}")
    print(f"EXPERIMENT: {config_name}")
    print(f"Ante={config.ante}, Bet Size={config.bet_size}, Iterations={num_iterations}")
    print(f"Nash Equilibrium Value: {nash_value:.6f}")
    print(f"{'='*70}")
    
    results = {}
    
    # 1. CFR (Baseline)
    print("\n  Training CFR...", end=" ", flush=True)
    cfr_trainer, cfr_values, cfr_time = run_silent(CFRTrainer, config, num_iterations)
    cfr_metrics = compute_metrics(cfr_values, nash_value)
    results['CFR'] = {'trainer': cfr_trainer, 'values': cfr_values, 'time': cfr_time, **cfr_metrics}
    print(f"Done ({cfr_time:.2f}s)")
    
    # 2. CFR+
    print("  Training CFR+...", end=" ", flush=True)
    cfr_plus_trainer, cfr_plus_values, cfr_plus_time = run_silent(CFRPlusTrainer, config, num_iterations, delay=0)
    cfr_plus_metrics = compute_metrics(cfr_plus_values, nash_value)
    results['CFR+'] = {'trainer': cfr_plus_trainer, 'values': cfr_plus_values, 'time': cfr_plus_time, **cfr_plus_metrics}
    print(f"Done ({cfr_plus_time:.2f}s)")
    
    # 3. NormalHedge
    print("  Training NormalHedge...", end=" ", flush=True)
    nh_trainer, nh_values, nh_time = run_silent(NormalHedgeTrainer, config, num_iterations)
    nh_metrics = compute_metrics(nh_values, nash_value)
    results['NormalHedge'] = {'trainer': nh_trainer, 'values': nh_values, 'time': nh_time, **nh_metrics}
    print(f"Done ({nh_time:.2f}s)")
    
    # 4. NormalHedge+
    print("  Training NormalHedge+...", end=" ", flush=True)
    nh_plus_trainer, nh_plus_values, nh_plus_time = run_silent(NormalHedgePlusTrainer, config, num_iterations)
    nh_plus_metrics = compute_metrics(nh_plus_values, nash_value)
    results['NormalHedge+'] = {'trainer': nh_plus_trainer, 'values': nh_plus_values, 'time': nh_plus_time, **nh_plus_metrics}
    print(f"Done ({nh_plus_time:.2f}s)")
    
    return results


def print_results_table(results, config_name):
    """Print results in a clean table format."""
    print(f"\n{'='*70}")
    print(f"RESULTS TABLE: {config_name}")
    print(f"{'='*70}")
    print(f"\n{'Algorithm':<15} {'Final Value':>12} {'Error':>12} {'Time (s)':>10} {'vs CFR':>10}")
    print("-" * 62)
    
    cfr_error = results['CFR']['error']
    cfr_time = results['CFR']['time']
    
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        r = results[alg_name]
        improvement = (cfr_error - r['error']) / cfr_error * 100 if cfr_error > 0 else 0
        speedup = cfr_time / r['time'] if r['time'] > 0 else 0
        
        improvement_str = f"{improvement:+.1f}%" if alg_name != 'CFR' else "baseline"
        print(f"{alg_name:<15} {r['final_value']:>12.6f} {r['error']:>12.6f} {r['time']:>10.2f} {improvement_str:>10}")
    
    print("-" * 62)


def print_strategy_comparison(results, info_sets_to_compare):
    """Print strategy comparison for key information sets."""
    print(f"\n{'='*70}")
    print("STRATEGY COMPARISON")
    print(f"{'='*70}")
    
    profiles = {}
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        profiles[alg_name] = results[alg_name]['trainer'].get_strategy_profile()
    
    for info_set in info_sets_to_compare:
        print(f"\n  Information Set: {info_set}")
        print(f"  {'-'*50}")
        
        if info_set in profiles['CFR']:
            actions = list(profiles['CFR'][info_set].keys())
            
            for action in actions:
                line = f"    {action:6s}: "
                for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
                    prob = profiles[alg_name].get(info_set, {}).get(action, 0)
                    line += f"{prob:.4f}  "
                print(line)


def plot_convergence_comparison(results, config_name, nash_value, filename):
    """
    Plot convergence comparison (running averages) for all algorithms.
    Similar to compare_cfr_variants.py plot.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    num_iterations = len(results['CFR']['values'])
    iterations = range(1, num_iterations + 1)
    
    # Plot 1: Running averages
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        running_avg = results[alg_name]['running_avg']
        ax1.plot(iterations, running_avg, 
                label=alg_name, 
                linewidth=2, 
                color=ALG_COLORS[alg_name],
                linestyle=ALG_STYLES[alg_name])
    
    # Add Nash equilibrium reference line
    ax1.axhline(y=nash_value, color='black', linestyle='--', 
               label='Nash Equilibrium', linewidth=2, alpha=0.5)
    
    ax1.set_xlabel('Iteration', fontsize=12)
    ax1.set_ylabel('Running Average Value', fontsize=12)
    ax1.set_title(f'{config_name}: Convergence Comparison (Running Average)', fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Error from Nash (log scale)
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        running_avg = results[alg_name]['running_avg']
        error = np.abs(running_avg - nash_value)
        ax2.plot(iterations, error, 
                label=alg_name, 
                linewidth=2, 
                color=ALG_COLORS[alg_name],
                linestyle=ALG_STYLES[alg_name])
    
    ax2.set_xlabel('Iteration', fontsize=12)
    ax2.set_ylabel('Absolute Error from Nash', fontsize=12)
    ax2.set_title(f'{config_name}: Convergence Speed (Error from Nash)', fontsize=14)
    ax2.set_yscale('log')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"  Plot saved: {filename}")
    plt.close()


def plot_error_bar_comparison(all_results, filename):
    """
    Plot bar chart comparing final errors across all configurations.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Prepare data
    configs = []
    alg_errors = {alg: [] for alg in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']}
    
    config_labels = {
        'std_10k': 'Standard\n10K',
        'std_100k': 'Standard\n100K',
        'lb_10k': 'Large Bet\n10K',
        'lb_100k': 'Large Bet\n100K',
        'la_10k': 'Large Ante\n10K',
        'la_100k': 'Large Ante\n100K',
        'sc_10k': 'Scaled\n10K',
        'sc_100k': 'Scaled\n100K'
    }
    
    for exp_name in ['std_10k', 'std_100k', 'lb_10k', 'lb_100k', 'la_10k', 'la_100k', 'sc_10k', 'sc_100k']:
        if exp_name in all_results:
            configs.append(config_labels[exp_name])
            for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
                alg_errors[alg_name].append(all_results[exp_name][alg_name]['error'])
    
    # Create grouped bar chart
    x = np.arange(len(configs))
    width = 0.2
    
    for i, alg_name in enumerate(['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']):
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, alg_errors[alg_name], width, 
                     label=alg_name, color=ALG_COLORS[alg_name], alpha=0.8)
    
    ax.set_xlabel('Configuration', fontsize=12)
    ax.set_ylabel('Error from Nash Equilibrium', fontsize=12)
    ax.set_title('Algorithm Comparison: Error Across Configurations', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"  Plot saved: {filename}")
    plt.close()


def plot_timing_comparison(all_results, filename):
    """
    Plot bar chart comparing training times across all configurations.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Prepare data
    configs = []
    alg_times = {alg: [] for alg in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']}
    
    config_labels = {
        'std_10k': 'Standard\n10K',
        'std_100k': 'Standard\n100K',
        'lb_10k': 'Large Bet\n10K',
        'lb_100k': 'Large Bet\n100K',
        'la_10k': 'Large Ante\n10K',
        'la_100k': 'Large Ante\n100K',
        'sc_10k': 'Scaled\n10K',
        'sc_100k': 'Scaled\n100K'
    }
    
    for exp_name in ['std_10k', 'std_100k', 'lb_10k', 'lb_100k', 'la_10k', 'la_100k', 'sc_10k', 'sc_100k']:
        if exp_name in all_results:
            configs.append(config_labels[exp_name])
            for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
                alg_times[alg_name].append(all_results[exp_name][alg_name]['time'])
    
    # Create grouped bar chart
    x = np.arange(len(configs))
    width = 0.2
    
    for i, alg_name in enumerate(['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']):
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, alg_times[alg_name], width, 
                     label=alg_name, color=ALG_COLORS[alg_name], alpha=0.8)
    
    ax.set_xlabel('Configuration', fontsize=12)
    ax.set_ylabel('Training Time (seconds)', fontsize=12)
    ax.set_title('Algorithm Comparison: Training Time Across Configurations', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"  Plot saved: {filename}")
    plt.close()


def plot_10k_vs_100k_comparison(results_10k, results_100k, config_name, filename):
    """
    Plot comparison between 10K and 100K iterations for the same configuration.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Top row: 10K iterations
    ax1, ax2 = axes[0]
    
    # Plot 10K running averages
    num_iter_10k = len(results_10k['CFR']['values'])
    iterations_10k = range(1, num_iter_10k + 1)
    
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        running_avg = results_10k[alg_name]['running_avg']
        ax1.plot(iterations_10k, running_avg, 
                label=alg_name, linewidth=2, 
                color=ALG_COLORS[alg_name], linestyle=ALG_STYLES[alg_name])
    
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Running Average Value')
    ax1.set_title(f'{config_name}: 10,000 Iterations')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 10K errors
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        running_avg = results_10k[alg_name]['running_avg']
        error = np.abs(running_avg - results_10k['CFR']['running_avg'][-1])
        ax2.plot(iterations_10k, np.abs(running_avg), 
                label=alg_name, linewidth=2,
                color=ALG_COLORS[alg_name], linestyle=ALG_STYLES[alg_name])
    
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('|Running Average|')
    ax2.set_title(f'{config_name}: 10K Convergence')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Bottom row: 100K iterations
    ax3, ax4 = axes[1]
    
    num_iter_100k = len(results_100k['CFR']['values'])
    iterations_100k = range(1, num_iter_100k + 1)
    
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        running_avg = results_100k[alg_name]['running_avg']
        ax3.plot(iterations_100k, running_avg, 
                label=alg_name, linewidth=2,
                color=ALG_COLORS[alg_name], linestyle=ALG_STYLES[alg_name])
    
    ax3.set_xlabel('Iteration')
    ax3.set_ylabel('Running Average Value')
    ax3.set_title(f'{config_name}: 100,000 Iterations (10x)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 100K errors
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        running_avg = results_100k[alg_name]['running_avg']
        ax4.plot(iterations_100k, np.abs(running_avg), 
                label=alg_name, linewidth=2,
                color=ALG_COLORS[alg_name], linestyle=ALG_STYLES[alg_name])
    
    ax4.set_xlabel('Iteration')
    ax4.set_ylabel('|Running Average|')
    ax4.set_title(f'{config_name}: 100K Convergence')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"  Plot saved: {filename}")
    plt.close()


def plot_final_summary(all_results, filename):
    """
    Create a comprehensive summary plot with multiple subplots.
    """
    fig = plt.figure(figsize=(18, 14))
    
    # Create grid layout
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.25)
    
    # Subplot 1: Error comparison bar chart (10K iterations only)
    ax1 = fig.add_subplot(gs[0, 0])
    configs_10k = ['std_10k', 'lb_10k', 'la_10k', 'sc_10k']
    config_labels_10k = ['Standard', 'Large Bet', 'Large Ante', 'Scaled']
    
    x = np.arange(len(configs_10k))
    width = 0.2
    
    for i, alg_name in enumerate(['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']):
        errors = [all_results[exp][alg_name]['error'] for exp in configs_10k if exp in all_results]
        offset = (i - 1.5) * width
        ax1.bar(x + offset, errors, width, label=alg_name, color=ALG_COLORS[alg_name], alpha=0.8)
    
    ax1.set_ylabel('Error from Nash')
    ax1.set_title('Error Comparison: 10K Iterations')
    ax1.set_xticks(x)
    ax1.set_xticklabels(config_labels_10k)
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Subplot 2: Error comparison bar chart (100K iterations only)
    ax2 = fig.add_subplot(gs[0, 1])
    configs_100k = ['std_100k', 'lb_100k', 'la_100k', 'sc_100k']
    
    for i, alg_name in enumerate(['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']):
        errors = [all_results[exp][alg_name]['error'] for exp in configs_100k if exp in all_results]
        offset = (i - 1.5) * width
        ax2.bar(x + offset, errors, width, label=alg_name, color=ALG_COLORS[alg_name], alpha=0.8)
    
    ax2.set_ylabel('Error from Nash')
    ax2.set_title('Error Comparison: 100K Iterations')
    ax2.set_xticks(x)
    ax2.set_xticklabels(config_labels_10k)
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Subplot 3: Running average convergence (Standard 100K)
    ax3 = fig.add_subplot(gs[1, 0])
    if 'std_100k' in all_results:
        results = all_results['std_100k']
        iterations = range(1, len(results['CFR']['values']) + 1)
        for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
            ax3.plot(iterations, results[alg_name]['running_avg'], 
                    label=alg_name, linewidth=2,
                    color=ALG_COLORS[alg_name], linestyle=ALG_STYLES[alg_name])
        ax3.axhline(y=-1/18, color='black', linestyle='--', alpha=0.5, label='Nash')
    ax3.set_xlabel('Iteration')
    ax3.set_ylabel('Running Average')
    ax3.set_title('Convergence: Standard Config (100K)')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Subplot 4: Error from Nash (log scale, Standard 100K)
    ax4 = fig.add_subplot(gs[1, 1])
    if 'std_100k' in all_results:
        results = all_results['std_100k']
        nash_value = -1/18
        for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
            error = np.abs(results[alg_name]['running_avg'] - nash_value)
            ax4.plot(iterations, error, 
                    label=alg_name, linewidth=2,
                    color=ALG_COLORS[alg_name], linestyle=ALG_STYLES[alg_name])
    ax4.set_xlabel('Iteration')
    ax4.set_ylabel('Error (log scale)')
    ax4.set_title('Convergence Speed: Standard Config (100K)')
    ax4.set_yscale('log')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # Subplot 5: Timing comparison
    ax5 = fig.add_subplot(gs[2, 0])
    all_configs = ['std_10k', 'std_100k', 'lb_10k', 'lb_100k']
    config_labels_time = ['Std 10K', 'Std 100K', 'LB 10K', 'LB 100K']
    x_time = np.arange(len(all_configs))
    
    for i, alg_name in enumerate(['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']):
        times = [all_results[exp][alg_name]['time'] for exp in all_configs if exp in all_results]
        offset = (i - 1.5) * width
        ax5.bar(x_time + offset, times, width, label=alg_name, color=ALG_COLORS[alg_name], alpha=0.8)
    
    ax5.set_ylabel('Time (seconds)')
    ax5.set_title('Training Time Comparison')
    ax5.set_xticks(x_time)
    ax5.set_xticklabels(config_labels_time)
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Subplot 6: Improvement over CFR
    ax6 = fig.add_subplot(gs[2, 1])
    improvements = {}
    for alg_name in ['CFR+', 'NormalHedge', 'NormalHedge+']:
        improvements[alg_name] = []
        for exp in configs_100k:
            if exp in all_results:
                cfr_err = all_results[exp]['CFR']['error']
                alg_err = all_results[exp][alg_name]['error']
                imp = (cfr_err - alg_err) / cfr_err * 100 if cfr_err > 0 else 0
                improvements[alg_name].append(imp)
    
    x_imp = np.arange(len(config_labels_10k))
    width_imp = 0.25
    
    for i, alg_name in enumerate(['CFR+', 'NormalHedge', 'NormalHedge+']):
        offset = (i - 1) * width_imp
        ax6.bar(x_imp + offset, improvements[alg_name], width_imp, 
               label=alg_name, color=ALG_COLORS[alg_name], alpha=0.8)
    
    ax6.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax6.set_ylabel('Improvement over CFR (%)')
    ax6.set_title('Improvement over CFR (100K iterations)')
    ax6.set_xticks(x_imp)
    ax6.set_xticklabels(config_labels_10k)
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Comprehensive Algorithm Comparison: CFR vs CFR+ vs NormalHedge vs NormalHedge+', 
                fontsize=16, fontweight='bold', y=1.02)
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"  Summary plot saved: {filename}")
    plt.close()


def main():
    """Run comprehensive experiments."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ALGORITHM COMPARISON EXPERIMENTS")
    print("=" * 70)
    print("\nThis script runs CFR, CFR+, NormalHedge, and NormalHedge+")
    print("under various game configurations and iteration counts.\n")
    
    all_results = {}
    
    # ===== EXPERIMENT SET 1: Standard Configuration =====
    print("\n" + "#" * 70)
    print("# EXPERIMENT SET 1: STANDARD KUHN POKER (Ante=1, Bet=1)")
    print("#" * 70)
    
    config_standard = GameConfig(ante=1, bet_size=1)
    nash_standard = -1/18  # Theoretical Nash equilibrium value
    
    # 1A: Standard iterations (10,000)
    results_std_10k = run_experiment(
        "Standard Config - 10,000 iterations",
        config_standard, 10000, nash_standard
    )
    print_results_table(results_std_10k, "Standard 10K")
    all_results['std_10k'] = results_std_10k
    
    # 1B: 10x iterations (100,000)
    results_std_100k = run_experiment(
        "Standard Config - 100,000 iterations (10x)",
        config_standard, 100000, nash_standard
    )
    print_results_table(results_std_100k, "Standard 100K")
    all_results['std_100k'] = results_std_100k
    
    # ===== EXPERIMENT SET 2: Larger Bet Size =====
    print("\n" + "#" * 70)
    print("# EXPERIMENT SET 2: LARGER BET SIZE (Ante=1, Bet=2)")
    print("#" * 70)
    
    config_large_bet = GameConfig(ante=1, bet_size=2)
    nash_large_bet = -1/18  # Approximate (exact Nash varies slightly with bet size)
    
    # 2A: Standard iterations
    results_lb_10k = run_experiment(
        "Large Bet (bet=2) - 10,000 iterations",
        config_large_bet, 10000, nash_large_bet
    )
    print_results_table(results_lb_10k, "Large Bet 10K")
    all_results['lb_10k'] = results_lb_10k
    
    # 2B: 10x iterations
    results_lb_100k = run_experiment(
        "Large Bet (bet=2) - 100,000 iterations (10x)",
        config_large_bet, 100000, nash_large_bet
    )
    print_results_table(results_lb_100k, "Large Bet 100K")
    all_results['lb_100k'] = results_lb_100k
    
    # ===== EXPERIMENT SET 3: Larger Ante =====
    print("\n" + "#" * 70)
    print("# EXPERIMENT SET 3: LARGER ANTE (Ante=2, Bet=1)")
    print("#" * 70)
    
    config_large_ante = GameConfig(ante=2, bet_size=1)
    nash_large_ante = -2/18  # Scales with ante
    
    # 3A: Standard iterations
    results_la_10k = run_experiment(
        "Large Ante (ante=2) - 10,000 iterations",
        config_large_ante, 10000, nash_large_ante
    )
    print_results_table(results_la_10k, "Large Ante 10K")
    all_results['la_10k'] = results_la_10k
    
    # 3B: 10x iterations
    results_la_100k = run_experiment(
        "Large Ante (ante=2) - 100,000 iterations (10x)",
        config_large_ante, 100000, nash_large_ante
    )
    print_results_table(results_la_100k, "Large Ante 100K")
    all_results['la_100k'] = results_la_100k
    
    # ===== EXPERIMENT SET 4: Scaled Up Game =====
    print("\n" + "#" * 70)
    print("# EXPERIMENT SET 4: SCALED UP GAME (Ante=2, Bet=2)")
    print("#" * 70)
    
    config_scaled = GameConfig(ante=2, bet_size=2)
    nash_scaled = -2/18
    
    # 4A: Standard iterations
    results_sc_10k = run_experiment(
        "Scaled Up (ante=2, bet=2) - 10,000 iterations",
        config_scaled, 10000, nash_scaled
    )
    print_results_table(results_sc_10k, "Scaled Up 10K")
    all_results['sc_10k'] = results_sc_10k
    
    # 4B: 10x iterations
    results_sc_100k = run_experiment(
        "Scaled Up (ante=2, bet=2) - 100,000 iterations (10x)",
        config_scaled, 100000, nash_scaled
    )
    print_results_table(results_sc_100k, "Scaled Up 100K")
    all_results['sc_100k'] = results_sc_100k
    
    # ===== STRATEGY COMPARISON =====
    print("\n" + "#" * 70)
    print("# STRATEGY COMPARISON (Standard Config, 100K iterations)")
    print("#" * 70)
    
    key_info_sets = ['J', 'Q', 'K', 'Jb', 'Qb', 'Kb', 'Jc', 'Qc', 'Kc']
    print_strategy_comparison(results_std_100k, key_info_sets)
    
    # ===== GENERATE PLOTS =====
    print("\n" + "#" * 70)
    print("# GENERATING COMPARISON PLOTS")
    print("#" * 70)
    
    # Convergence plots for each configuration
    print("\n  Generating convergence plots...")
    plot_convergence_comparison(results_std_10k, "Standard Config (10K)", nash_standard, 
                                'exp_convergence_std_10k.png')
    plot_convergence_comparison(results_std_100k, "Standard Config (100K)", nash_standard, 
                                'exp_convergence_std_100k.png')
    plot_convergence_comparison(results_lb_100k, "Large Bet Config (100K)", nash_large_bet, 
                                'exp_convergence_lb_100k.png')
    plot_convergence_comparison(results_la_100k, "Large Ante Config (100K)", nash_large_ante, 
                                'exp_convergence_la_100k.png')
    plot_convergence_comparison(results_sc_100k, "Scaled Up Config (100K)", nash_scaled, 
                                'exp_convergence_sc_100k.png')
    
    # 10K vs 100K comparison plots
    print("\n  Generating 10K vs 100K comparison plots...")
    plot_10k_vs_100k_comparison(results_std_10k, results_std_100k, "Standard Config", 
                                'exp_10k_vs_100k_standard.png')
    plot_10k_vs_100k_comparison(results_lb_10k, results_lb_100k, "Large Bet Config", 
                                'exp_10k_vs_100k_largebet.png')
    
    # Error and timing bar charts
    print("\n  Generating summary bar charts...")
    plot_error_bar_comparison(all_results, 'exp_error_comparison.png')
    plot_timing_comparison(all_results, 'exp_timing_comparison.png')
    
    # Final comprehensive summary plot
    print("\n  Generating comprehensive summary plot...")
    plot_final_summary(all_results, 'exp_comprehensive_summary.png')
    
    # ===== SUMMARY =====
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    print("\n| Configuration      | Iters | CFR Error | CFR+ Error | NH Error  | NH+ Error |")
    print("|" + "-" * 20 + "|" + "-" * 7 + "|" + "-" * 11 + "|" + "-" * 12 + "|" + "-" * 11 + "|" + "-" * 11 + "|")
    
    for exp_name, exp_results in all_results.items():
        iters = "100K" if "100k" in exp_name else "10K"
        if "std" in exp_name:
            config = "Standard (1,1)"
        elif "lb" in exp_name:
            config = "Large Bet (1,2)"
        elif "la" in exp_name:
            config = "Large Ante (2,1)"
        else:
            config = "Scaled (2,2)"
        
        cfr_err = exp_results['CFR']['error']
        cfrp_err = exp_results['CFR+']['error']
        nh_err = exp_results['NormalHedge']['error']
        nhp_err = exp_results['NormalHedge+']['error']
        
        print(f"| {config:<18} | {iters:<5} | {cfr_err:>9.6f} | {cfrp_err:>10.6f} | {nh_err:>9.6f} | {nhp_err:>9.6f} |")
    
    print("\n" + "=" * 70)
    print("EXPERIMENTS COMPLETE")
    print("=" * 70)
    
    print("\nGenerated plot files:")
    print("  - exp_convergence_std_10k.png      : Standard config, 10K iterations convergence")
    print("  - exp_convergence_std_100k.png     : Standard config, 100K iterations convergence")
    print("  - exp_convergence_lb_100k.png      : Large bet config, 100K iterations convergence")
    print("  - exp_convergence_la_100k.png      : Large ante config, 100K iterations convergence")
    print("  - exp_convergence_sc_100k.png      : Scaled up config, 100K iterations convergence")
    print("  - exp_10k_vs_100k_standard.png     : Standard config, 10K vs 100K comparison")
    print("  - exp_10k_vs_100k_largebet.png     : Large bet config, 10K vs 100K comparison")
    print("  - exp_error_comparison.png         : Error comparison bar chart (all configs)")
    print("  - exp_timing_comparison.png        : Timing comparison bar chart (all configs)")
    print("  - exp_comprehensive_summary.png    : Comprehensive summary with all plots")
    print("\n")


if __name__ == "__main__":
    main()

