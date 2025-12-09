"""
Main script to run CFR or CFR+ on Kuhn Poker and visualize results.
"""
import numpy as np
import matplotlib.pyplot as plt
from kuhn_poker import GameConfig
from cfr import CFRTrainer
from cfr_plus import CFRPlusTrainer
import json


def estimate_nash_value(config: GameConfig, estimation_iterations: int = 10000) -> float:
    """
    Empirically estimate the Nash equilibrium value for a given configuration.
    
    Args:
        config: Game configuration
        estimation_iterations: Number of CFR iterations to run for estimation
    
    Returns:
        Estimated Nash equilibrium value
    
    Note:
        For accurate estimates, use at least 10,000 iterations.
        More iterations = better estimate, but takes longer.
    """
    print(f"  Estimating Nash value for config (ante={config.ante}, bet_size={config.bet_size})...")
    print(f"  Running {estimation_iterations} CFR iterations (this may take 1-2 minutes)...")
    
    trainer = CFRTrainer(config)
    values = trainer.train(estimation_iterations)
    
    # Use last 30% of iterations for estimate (more stable)
    estimation_window = max(2000, estimation_iterations // 3)
    nash_estimate = np.mean(values[-estimation_window:])
    
    # Calculate standard deviation to show confidence
    nash_std = np.std(values[-estimation_window:])
    
    print(f"  Estimated Nash value: {nash_estimate:.6f} (±{nash_std:.6f})")
    print(f"  Confidence: {'Good' if nash_std < 0.5 else 'Low - consider more iterations'}")
    
    return nash_estimate


def plot_convergence(expected_values: list, window_size: int = 100, nash_value: float = None, config: GameConfig = None):
    """
    Plot the convergence of the CFR algorithm.
    
    Args:
        expected_values: List of expected game values per iteration
        window_size: Window size for moving average smoothing
        nash_value: Nash equilibrium value to plot as reference (if None, uses -1/18)
        config: Game configuration (for label)
    """
    if nash_value is None:
        nash_value = -1/18
    
    if config is None:
        config_label = "ante=1, bet=1"
    else:
        config_label = f"ante={config.ante}, bet={config.bet_size}"
    iterations = range(1, len(expected_values) + 1)
    
    # Calculate running average
    running_avg = []
    cumsum = 0
    for i, val in enumerate(expected_values):
        cumsum += val
        running_avg.append(cumsum / (i + 1))
    
    # Calculate moving average for smoothing
    moving_avg = []
    for i in range(len(expected_values)):
        start_idx = max(0, i - window_size + 1)
        window = expected_values[start_idx:i + 1]
        moving_avg.append(np.mean(window))
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Expected values and moving average
    ax1.plot(iterations, expected_values, alpha=0.3, label='Per-iteration value', linewidth=0.5)
    ax1.plot(iterations, moving_avg, label=f'Moving average (window={window_size})', linewidth=2)
    ax1.axhline(y=nash_value, color='r', linestyle='--', 
                label=f'Nash value ({config_label}): {nash_value:.4f}', linewidth=2)
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Expected Value (Player 0)')
    ax1.set_title('CFR Convergence: Expected Game Value')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Running average (cumulative)
    ax2.plot(iterations, running_avg, label='Cumulative average', linewidth=2)
    ax2.axhline(y=nash_value, color='r', linestyle='--', 
                label=f'Nash value ({config_label}): {nash_value:.4f}', linewidth=2)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Running Average Value')
    ax2.set_title('CFR Convergence: Running Average')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('cfr_convergence.png', dpi=300, bbox_inches='tight')
    print(f"\nConvergence plot saved to: cfr_convergence.png")
    plt.show()


def print_strategy_profile(profile: dict):
    """
    Pretty print the strategy profile.
    """
    print("\n" + "="*70)
    print("LEARNED STRATEGY PROFILE")
    print("="*70)
    
    # Organize by player and card
    for player in [0, 1]:
        print(f"\nPLAYER {player} STRATEGIES:")
        print("-" * 70)
        
        for card in ['J', 'Q', 'K']:
            card_strategies = {k: v for k, v in profile.items() if k.startswith(card)}
            
            if card_strategies:
                print(f"\n  Card: {card}")
                for info_set, actions in sorted(card_strategies.items()):
                    history = info_set[1:] if len(info_set) > 1 else "(start)"
                    print(f"    History: {history if history else '(start)'}")
                    for action, prob in actions.items():
                        print(f"      {action}: {prob:.4f}")


def compare_strategies(trainer: CFRTrainer):
    """
    Compare strategies across different cards to identify patterns.
    """
    print("\n" + "="*70)
    print("STRATEGY ANALYSIS")
    print("="*70)
    
    profile = trainer.get_strategy_profile()
    
    # Analyze initial actions (no history)
    print("\nInitial Action (Player 0):")
    for card in ['J', 'Q', 'K']:
        key = f"{card}"
        if key in profile:
            print(f"  {card}: BET={profile[key]['BET']:.4f}, CHECK={profile[key]['CHECK']:.4f}")
    
    # Analyze responses to bet
    print("\nResponse to Bet (Player 1):")
    for card in ['J', 'Q', 'K']:
        key = f"{card}b"
        if key in profile:
            print(f"  {card}: CALL={profile[key]['CALL']:.4f}, FOLD={profile[key]['FOLD']:.4f}")
    
    # Analyze check-bet response
    print("\nResponse to Check-Bet (Player 0):")
    for card in ['J', 'Q', 'K']:
        key = f"{card}cb"
        if key in profile:
            print(f"  {card}: CALL={profile[key]['CALL']:.4f}, FOLD={profile[key]['FOLD']:.4f}")


def save_results(trainer: CFRTrainer, expected_values: list, filename: str = "cfr_results.json"):
    """
    Save the results to a JSON file.
    """
    results = {
        "config": {
            "ante": trainer.config.ante,
            "bet_size": trainer.config.bet_size
        },
        "strategy_profile": trainer.get_strategy_profile(),
        "final_expected_value": float(np.mean(expected_values[-1000:])),
        "num_iterations": len(expected_values)
    }
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {filename}")


def main(auto_estimate_nash: bool = True, algorithm: str = "CFR", cfr_plus_delay: int = 0):
    """
    Main function to run CFR or CFR+ training on Kuhn Poker.
    
    Args:
        auto_estimate_nash: If True, automatically estimate Nash value for non-standard configs.
                           If False, use -1/18 for all configs (faster but may be inaccurate).
        algorithm: Algorithm to use - "CFR" for vanilla CFR or "CFR+" for CFR+
        cfr_plus_delay: Delay parameter for CFR+ (only used if algorithm="CFR+")
    """
    print("="*70)
    if algorithm == "CFR+":
        print(f"COUNTERFACTUAL REGRET MINIMIZATION PLUS (CFR+) FOR KUHN POKER")
        print(f"Delay parameter: {cfr_plus_delay}")
    else:
        print("COUNTERFACTUAL REGRET MINIMIZATION (CFR) FOR KUHN POKER")
    print("="*70)
    
    # Configuration
    config = GameConfig(ante=1, bet_size=3)
    num_iterations = 100000
    
    print(f"\nConfiguration:")
    print(f"  Algorithm: {algorithm}")
    print(f"  Ante: {config.ante}")
    print(f"  Bet size: {config.bet_size}")
    print(f"  Number of iterations: {num_iterations}")
    if algorithm == "CFR+":
        print(f"  Delay (d): {cfr_plus_delay}")
        print(f"  Weight formula: w = max{{t - {cfr_plus_delay}, 0}}")
    
    # Estimate Nash value for any configuration
    print(f"\nPreparing Nash equilibrium reference...")
    if config.ante == 1 and config.bet_size == 1:
        # Use known theoretical value for standard Kuhn Poker
        nash_value = -1/18
        print(f"  Using known theoretical value: {nash_value:.6f}")
    elif auto_estimate_nash:
        # Empirically estimate Nash value for non-standard configurations
        print(f"  Non-standard configuration detected.")
        nash_value = estimate_nash_value(config, estimation_iterations=10000)
    else:
        # Use standard value (may be inaccurate for non-standard configs)
        nash_value = -1/18
        print(f"  Using standard value: {nash_value:.6f}")
        print(f"  ⚠️  WARNING: This may not be accurate for your configuration!")
    
    print(f"\nStarting main {algorithm} training...\n")
    
    # Initialize trainer based on algorithm choice
    if algorithm == "CFR+":
        trainer = CFRPlusTrainer(config, delay=cfr_plus_delay)
    else:
        trainer = CFRTrainer(config)
    
    # Train
    expected_values = trainer.train(num_iterations)
    
    # Calculate final statistics
    final_avg = np.mean(expected_values[-1000:])
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"Final expected value (avg of last 1000): {final_avg:.6f}")
    print(f"Nash equilibrium value: {nash_value:.6f}")
    print(f"Difference: {abs(final_avg - nash_value):.6f}")
    
    # Display strategy profile
    print_strategy_profile(trainer.get_strategy_profile())
    
    # Strategy analysis
    compare_strategies(trainer)
    
    # Save results
    save_results(trainer, expected_values)
    
    # Plot convergence with correct Nash value
    plot_convergence(expected_values, window_size=100, nash_value=nash_value, config=config)


if __name__ == "__main__":
    # Run with vanilla CFR (default)
    main(algorithm="CFR")
    
    # To run with CFR+ instead, uncomment one of these:
    # main(algorithm="CFR+", cfr_plus_delay=0)     # CFR+ with no delay
    # main(algorithm="CFR+", cfr_plus_delay=100)   # CFR+ with delay=100
    # main(algorithm="CFR+", cfr_plus_delay=500)   # CFR+ with delay=500

