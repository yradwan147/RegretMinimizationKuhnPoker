"""
Experiment script for testing different Kuhn Poker configurations.
This demonstrates how to modify game rules and compare results.
"""
import numpy as np
import matplotlib.pyplot as plt
from kuhn_poker import GameConfig
from cfr import CFRTrainer


def experiment_bet_sizes():
    """
    Experiment with different bet sizes and compare convergence.
    """
    print("="*70)
    print("EXPERIMENT: Different Bet Sizes")
    print("="*70)
    
    bet_sizes = [1, 2, 3, 5]
    num_iterations = 5000
    
    results = {}
    
    for bet_size in bet_sizes:
        print(f"\nTraining with bet_size={bet_size}...")
        config = GameConfig(ante=1, bet_size=bet_size)
        trainer = CFRTrainer(config)
        expected_values = trainer.train(num_iterations)
        
        final_value = np.mean(expected_values[-500:])
        results[bet_size] = {
            'values': expected_values,
            'final': final_value,
            'trainer': trainer
        }
        
        print(f"  Final expected value: {final_value:.6f}")
    
    # Plot comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Plot convergence curves
    for bet_size, data in results.items():
        # Calculate running average
        running_avg = []
        cumsum = 0
        for i, val in enumerate(data['values']):
            cumsum += val
            running_avg.append(cumsum / (i + 1))
        
        ax1.plot(running_avg, label=f'Bet size = {bet_size}', linewidth=2)
    
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Running Average Value')
    ax1.set_title('Convergence Comparison: Different Bet Sizes')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot final values
    bet_sizes_list = list(results.keys())
    final_values = [results[bs]['final'] for bs in bet_sizes_list]
    
    ax2.bar([str(bs) for bs in bet_sizes_list], final_values, color='skyblue', edgecolor='navy')
    ax2.set_xlabel('Bet Size')
    ax2.set_ylabel('Final Expected Value')
    ax2.set_title('Final Values by Bet Size')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('experiment_bet_sizes.png', dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: experiment_bet_sizes.png")
    plt.show()
    
    return results


def experiment_iterations():
    """
    Experiment with different numbers of iterations to see convergence rate.
    """
    print("\n" + "="*70)
    print("EXPERIMENT: Convergence Rate Analysis")
    print("="*70)
    
    iteration_counts = [1000, 2000, 5000, 10000, 20000]
    config = GameConfig(ante=1, bet_size=1)
    theoretical_value = -1/18  # Only valid for ante=1, bet_size=1
    
    errors = []
    
    for num_iter in iteration_counts:
        print(f"\nTraining with {num_iter} iterations...")
        trainer = CFRTrainer(config)
        expected_values = trainer.train(num_iter)
        
        final_value = np.mean(expected_values[-min(500, num_iter//10):])
        error = abs(final_value - theoretical_value)
        errors.append(error)
        
        print(f"  Final value: {final_value:.6f}")
        print(f"  Error from Nash: {error:.6f}")
    
    # Plot error vs iterations
    plt.figure(figsize=(10, 6))
    plt.plot(iteration_counts, errors, 'o-', linewidth=2, markersize=8)
    plt.xlabel('Number of Iterations')
    plt.ylabel('Error from Nash Equilibrium')
    plt.title('Convergence Rate: Error vs Iterations')
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.yscale('log')
    
    # Add theoretical O(1/sqrt(T)) line
    theoretical_errors = [errors[0] * np.sqrt(iteration_counts[0] / it) for it in iteration_counts]
    plt.plot(iteration_counts, theoretical_errors, '--', label='O(1/√T) theoretical', linewidth=2)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('experiment_convergence_rate.png', dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: experiment_convergence_rate.png")
    plt.show()


def analyze_strategy_evolution():
    """
    Show how strategies evolve over time.
    """
    print("\n" + "="*70)
    print("EXPERIMENT: Strategy Evolution")
    print("="*70)
    
    config = GameConfig(ante=1, bet_size=1)
    num_iterations = 10000
    checkpoints = [100, 500, 1000, 2000, 5000, 10000]
    
    # We'll track the strategy at specific checkpoints
    strategies_over_time = {cp: None for cp in checkpoints}
    
    print(f"\nTraining with checkpoints at: {checkpoints}")
    trainer = CFRTrainer(config)
    
    for i in range(num_iterations):
        # Deal random cards
        deck = config.get_deck()
        cards = [deck[0], deck[1]]
        
        # Create initial game state
        from kuhn_poker import GameState
        initial_state = GameState(config, cards)
        
        # Run CFR
        trainer.cfr(initial_state, reach_prob_0=1.0, reach_prob_1=1.0)
        
        # Save strategy at checkpoints
        if (i + 1) in checkpoints:
            strategies_over_time[i + 1] = trainer.get_strategy_profile()
            print(f"  Checkpoint {i + 1} saved")
    
    # Analyze a specific information set (e.g., King at start for Player 0)
    info_set_key = "K"  # King card, no history
    bet_probs = []
    
    for checkpoint in checkpoints:
        strategy = strategies_over_time[checkpoint]
        if info_set_key in strategy:
            bet_prob = strategy[info_set_key].get('BET', 0.5)
            bet_probs.append(bet_prob)
        else:
            bet_probs.append(0.5)
    
    # Plot strategy evolution
    plt.figure(figsize=(10, 6))
    plt.plot(checkpoints, bet_probs, 'o-', linewidth=2, markersize=8, color='darkblue')
    plt.xlabel('Iteration')
    plt.ylabel('Probability of Betting')
    plt.title('Strategy Evolution: P(Bet | King, Start)')
    plt.grid(True, alpha=0.3)
    plt.ylim([0, 1])
    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Optimal (always bet)')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('experiment_strategy_evolution.png', dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: experiment_strategy_evolution.png")
    plt.show()


def compare_initial_strategies():
    """
    Compare initial action strategies for all three cards.
    """
    print("\n" + "="*70)
    print("EXPERIMENT: Initial Action Strategies by Card")
    print("="*70)
    
    config = GameConfig(ante=1, bet_size=1)
    trainer = CFRTrainer(config)
    
    print("\nTraining...")
    trainer.train(10000)
    
    profile = trainer.get_strategy_profile()
    
    # Extract initial action probabilities
    cards = ['J', 'Q', 'K']
    bet_probs = []
    check_probs = []
    
    for card in cards:
        if card in profile:
            bet_probs.append(profile[card].get('BET', 0))
            check_probs.append(profile[card].get('CHECK', 0))
        else:
            bet_probs.append(0)
            check_probs.append(1)
    
    # Create bar chart
    x = np.arange(len(cards))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, check_probs, width, label='Check', color='lightblue', edgecolor='navy')
    rects2 = ax.bar(x + width/2, bet_probs, width, label='Bet', color='lightcoral', edgecolor='darkred')
    
    ax.set_ylabel('Probability')
    ax.set_title('Learned Initial Action Strategy by Card')
    ax.set_xticks(x)
    ax.set_xticklabels(cards)
    ax.legend()
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(rect.get_x() + rect.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig('experiment_initial_strategies.png', dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: experiment_initial_strategies.png")
    plt.show()


def main():
    """
    Run all experiments.
    """
    print("\n")
    print("="*70)
    print("KUHN POKER CFR EXPERIMENTS")
    print("="*70)
    print("\nThis script runs several experiments to demonstrate:")
    print("  1. Effect of different bet sizes")
    print("  2. Convergence rate analysis")
    print("  3. Strategy evolution over time")
    print("  4. Final strategy comparison by card")
    print("\n")
    
    # Run experiments
    experiment_bet_sizes()
    experiment_iterations()
    analyze_strategy_evolution()
    compare_initial_strategies()
    
    print("\n" + "="*70)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - experiment_bet_sizes.png")
    print("  - experiment_convergence_rate.png")
    print("  - experiment_strategy_evolution.png")
    print("  - experiment_initial_strategies.png")
    print("\n")


if __name__ == "__main__":
    main()

