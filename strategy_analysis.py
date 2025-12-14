"""
Strategy Convergence Analysis
Analyze how strategies converge to Nash equilibrium across iterations.
"""
import numpy as np
import matplotlib.pyplot as plt
from kuhn_poker import GameConfig
from cfr import CFRTrainer
from cfr_plus import CFRPlusTrainer
from normal_hedge import NormalHedgeTrainer
from normal_hedge_plus import NormalHedgePlusTrainer
import sys
from io import StringIO

# Nash equilibrium strategies for standard Kuhn Poker
NASH_EQUILIBRIUM = {
    # Player 0 initial (optimal: J bluffs 1/3, Q always checks, K bets ~3× alpha)
    'J': {'CHECK': 2/3, 'BET': 1/3},  # Bluff with probability 1/3
    'Q': {'CHECK': 1.0, 'BET': 0.0},  # Always check
    'K': {'CHECK': 0.0, 'BET': 1.0},  # Always bet (can be [0, 1/3] check)
    
    # Player 1 after check
    'Jc': {'CHECK': 2/3, 'BET': 1/3},  # Bluff with 1/3
    'Qc': {'CHECK': 1.0, 'BET': 0.0},  # Check
    'Kc': {'CHECK': 0.0, 'BET': 1.0},  # Always bet
    
    # Player 1 facing bet
    'Jb': {'FOLD': 1.0, 'CALL': 0.0},  # Always fold
    'Qb': {'FOLD': 2/3, 'CALL': 1/3},  # Call with 1/3
    'Kb': {'FOLD': 0.0, 'CALL': 1.0},  # Always call
    
    # Player 0 facing bet after check
    'Jcb': {'FOLD': 1.0, 'CALL': 0.0},  # Always fold
    'Qcb': {'FOLD': 2/3, 'CALL': 1/3},  # Call with 1/3
    'Kcb': {'FOLD': 0.0, 'CALL': 1.0},  # Always call
}


def run_silent(trainer_class, config, num_iterations, **kwargs):
    """Run training silently."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    trainer = trainer_class(config, **kwargs) if kwargs else trainer_class(config)
    trainer.train(num_iterations)
    
    sys.stdout = old_stdout
    return trainer


def get_strategy_distance(profile, nash):
    """Calculate L2 distance between learned strategy and Nash equilibrium."""
    total_distance = 0
    count = 0
    
    for info_set, nash_strat in nash.items():
        if info_set in profile:
            learned = profile[info_set]
            for action, nash_prob in nash_strat.items():
                learned_prob = learned.get(action, 0)
                total_distance += (nash_prob - learned_prob) ** 2
                count += 1
    
    return np.sqrt(total_distance / count) if count > 0 else 0


def analyze_strategy_convergence():
    """Analyze how strategies converge over iterations."""
    config = GameConfig(ante=1, bet_size=1)
    
    # Iteration checkpoints
    checkpoints = [1000, 5000, 10000, 25000, 50000, 100000]
    
    results = {
        'CFR': {'distances': [], 'strategies': {}},
        'CFR+': {'distances': [], 'strategies': {}},
        'NormalHedge': {'distances': [], 'strategies': {}},
        'NormalHedge+': {'distances': [], 'strategies': {}}
    }
    
    algorithms = [
        ('CFR', CFRTrainer, {}),
        ('CFR+', CFRPlusTrainer, {'delay': 0}),
        ('NormalHedge', NormalHedgeTrainer, {}),
        ('NormalHedge+', NormalHedgePlusTrainer, {})
    ]
    
    for alg_name, trainer_class, kwargs in algorithms:
        print(f"\nAnalyzing {alg_name}...")
        
        for checkpoint in checkpoints:
            print(f"  Training for {checkpoint} iterations...", end=" ", flush=True)
            trainer = run_silent(trainer_class, config, checkpoint, **kwargs)
            profile = trainer.get_strategy_profile()
            
            distance = get_strategy_distance(profile, NASH_EQUILIBRIUM)
            results[alg_name]['distances'].append(distance)
            results[alg_name]['strategies'][checkpoint] = profile
            print(f"Distance from Nash: {distance:.4f}")
    
    return results, checkpoints


def print_strategy_comparison_table(results, checkpoints):
    """Print detailed strategy comparison table."""
    print("\n" + "="*80)
    print("STRATEGY CONVERGENCE ANALYSIS")
    print("="*80)
    
    # Key information sets to analyze
    key_info_sets = [
        ('J', 'BET', 1/3, 'Bluff probability'),
        ('Q', 'CHECK', 1.0, 'Check probability'),
        ('K', 'BET', 1.0, 'Value bet probability'),
        ('Jb', 'FOLD', 1.0, 'Fold to bet'),
        ('Kb', 'CALL', 1.0, 'Call with King'),
    ]
    
    print("\n--- Key Strategy Comparison (100K iterations) ---")
    print(f"\n{'Info Set':<10} {'Action':<8} {'Nash':<8} {'CFR':<10} {'CFR+':<10} {'NH':<10} {'NH+':<10}")
    print("-" * 70)
    
    final_checkpoint = checkpoints[-1]
    
    for info_set, action, nash_prob, description in key_info_sets:
        cfr_prob = results['CFR']['strategies'][final_checkpoint].get(info_set, {}).get(action, 0)
        cfrp_prob = results['CFR+']['strategies'][final_checkpoint].get(info_set, {}).get(action, 0)
        nh_prob = results['NormalHedge']['strategies'][final_checkpoint].get(info_set, {}).get(action, 0)
        nhp_prob = results['NormalHedge+']['strategies'][final_checkpoint].get(info_set, {}).get(action, 0)
        
        print(f"{info_set:<10} {action:<8} {nash_prob:<8.3f} {cfr_prob:<10.4f} {cfrp_prob:<10.4f} {nh_prob:<10.4f} {nhp_prob:<10.4f}")
    
    print("\n--- Distance from Nash Equilibrium ---")
    print(f"\n{'Iterations':<12} {'CFR':<12} {'CFR+':<12} {'NH':<12} {'NH+':<12}")
    print("-" * 60)
    
    for i, checkpoint in enumerate(checkpoints):
        cfr_d = results['CFR']['distances'][i]
        cfrp_d = results['CFR+']['distances'][i]
        nh_d = results['NormalHedge']['distances'][i]
        nhp_d = results['NormalHedge+']['distances'][i]
        print(f"{checkpoint:<12} {cfr_d:<12.4f} {cfrp_d:<12.4f} {nh_d:<12.4f} {nhp_d:<12.4f}")


def plot_strategy_convergence(results, checkpoints):
    """Create visualization of strategy convergence."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    colors = {'CFR': 'blue', 'CFR+': 'red', 'NormalHedge': 'purple', 'NormalHedge+': 'magenta'}
    
    # Plot 1: Overall distance from Nash
    ax = axes[0, 0]
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        ax.plot(checkpoints, results[alg_name]['distances'], 
                marker='o', label=alg_name, color=colors[alg_name], linewidth=2)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('L2 Distance from Nash')
    ax.set_title('Overall Strategy Distance from Nash Equilibrium')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Jack bluffing probability (should be 1/3)
    ax = axes[0, 1]
    nash_j_bet = 1/3
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        probs = [results[alg_name]['strategies'][cp].get('J', {}).get('BET', 0) for cp in checkpoints]
        ax.plot(checkpoints, probs, marker='o', label=alg_name, color=colors[alg_name], linewidth=2)
    ax.axhline(y=nash_j_bet, color='black', linestyle='--', label='Nash (1/3)', linewidth=2)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Probability')
    ax.set_title('Jack Bluffing Probability (Nash = 1/3)')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: King betting probability (should be ~1)
    ax = axes[0, 2]
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        probs = [results[alg_name]['strategies'][cp].get('K', {}).get('BET', 0) for cp in checkpoints]
        ax.plot(checkpoints, probs, marker='o', label=alg_name, color=colors[alg_name], linewidth=2)
    ax.axhline(y=1.0, color='black', linestyle='--', label='Nash (1.0)', linewidth=2)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Probability')
    ax.set_title('King Value Betting Probability (Nash ≥ 2/3)')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Queen checking probability (should be 1)
    ax = axes[1, 0]
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        probs = [results[alg_name]['strategies'][cp].get('Q', {}).get('CHECK', 0) for cp in checkpoints]
        ax.plot(checkpoints, probs, marker='o', label=alg_name, color=colors[alg_name], linewidth=2)
    ax.axhline(y=1.0, color='black', linestyle='--', label='Nash (1.0)', linewidth=2)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Probability')
    ax.set_title('Queen Checking Probability (Nash = 1.0)')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 5: Jack folding to bet (should be 1)
    ax = axes[1, 1]
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        probs = [results[alg_name]['strategies'][cp].get('Jb', {}).get('FOLD', 0) for cp in checkpoints]
        ax.plot(checkpoints, probs, marker='o', label=alg_name, color=colors[alg_name], linewidth=2)
    ax.axhline(y=1.0, color='black', linestyle='--', label='Nash (1.0)', linewidth=2)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Probability')
    ax.set_title('Jack Folding to Bet (Nash = 1.0)')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Queen calling with bet (should be 1/3)
    ax = axes[1, 2]
    nash_qb_call = 1/3
    for alg_name in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
        probs = [results[alg_name]['strategies'][cp].get('Qb', {}).get('CALL', 0) for cp in checkpoints]
        ax.plot(checkpoints, probs, marker='o', label=alg_name, color=colors[alg_name], linewidth=2)
    ax.axhline(y=nash_qb_call, color='black', linestyle='--', label='Nash (1/3)', linewidth=2)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Probability')
    ax.set_title('Queen Calling a Bet (Nash = 1/3)')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.suptitle('Strategy Convergence to Nash Equilibrium', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('strategy_convergence_analysis.png', dpi=300, bbox_inches='tight')
    print("\nSaved: strategy_convergence_analysis.png")
    plt.close()


def generate_latex_table(results, checkpoints):
    """Generate LaTeX table for strategy convergence."""
    print("\n\n--- LaTeX Table: Strategy Distance from Nash ---")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{L2 distance from Nash equilibrium strategies across iterations.}")
    print(r"\label{tab:strategy_distance}")
    print(r"\small")
    print(r"\begin{tabular}{rcccc}")
    print(r"\toprule")
    print(r"Iterations & CFR & CFR+ & NormalHedge & NormalHedge+ \\")
    print(r"\midrule")
    
    for i, checkpoint in enumerate(checkpoints):
        cfr_d = results['CFR']['distances'][i]
        cfrp_d = results['CFR+']['distances'][i]
        nh_d = results['NormalHedge']['distances'][i]
        nhp_d = results['NormalHedge+']['distances'][i]
        
        # Find minimum
        min_d = min(cfr_d, cfrp_d, nh_d, nhp_d)
        
        def fmt(d):
            if d == min_d:
                return r"\textbf{" + f"{d:.4f}" + "}"
            return f"{d:.4f}"
        
        print(f"{checkpoint:,} & {fmt(cfr_d)} & {fmt(cfrp_d)} & {fmt(nh_d)} & {fmt(nhp_d)} \\\\")
    
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")
    
    # Key strategies table
    print("\n\n--- LaTeX Table: Key Strategy Comparison ---")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Learned strategies for key decision points (100K iterations). Bold indicates closest to Nash.}")
    print(r"\label{tab:key_strategies}")
    print(r"\small")
    print(r"\begin{tabular}{llcccccc}")
    print(r"\toprule")
    print(r"Info Set & Action & Nash & CFR & CFR+ & NH & NH+ \\")
    print(r"\midrule")
    
    key_info_sets = [
        ('J', 'BET', 1/3),
        ('Q', 'CHECK', 1.0),
        ('K', 'BET', 1.0),
        ('Jb', 'FOLD', 1.0),
        ('Qb', 'CALL', 1/3),
        ('Kb', 'CALL', 1.0),
        ('Jcb', 'FOLD', 1.0),
        ('Kcb', 'CALL', 1.0),
    ]
    
    final_cp = checkpoints[-1]
    
    for info_set, action, nash_prob in key_info_sets:
        probs = {}
        for alg in ['CFR', 'CFR+', 'NormalHedge', 'NormalHedge+']:
            probs[alg] = results[alg]['strategies'][final_cp].get(info_set, {}).get(action, 0)
        
        # Find closest to Nash
        errors = {alg: abs(p - nash_prob) for alg, p in probs.items()}
        min_error = min(errors.values())
        
        def fmt(alg):
            p = probs[alg]
            if errors[alg] == min_error:
                return r"\textbf{" + f"{p:.3f}" + "}"
            return f"{p:.3f}"
        
        print(f"{info_set} & {action} & {nash_prob:.3f} & {fmt('CFR')} & {fmt('CFR+')} & {fmt('NormalHedge')} & {fmt('NormalHedge+')} \\\\")
    
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")


if __name__ == "__main__":
    print("="*60)
    print("STRATEGY CONVERGENCE ANALYSIS")
    print("="*60)
    
    results, checkpoints = analyze_strategy_convergence()
    print_strategy_comparison_table(results, checkpoints)
    plot_strategy_convergence(results, checkpoints)
    generate_latex_table(results, checkpoints)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

