# Counterfactual Regret Minimization for Kuhn Poker

A tree-based implementation of Counterfactual Regret Minimization (CFR) applied to Kuhn Poker, designed for easy experimentation with game rules and algorithm parameters.

## Overview

This implementation provides:
- **Tree-based CFR**: Clean game tree structure for transparent game logic
- **Configurable rules**: Easy modification of antes, bet sizes, and game mechanics
- **Strategy visualization**: Clear output of learned strategies
- **Convergence analysis**: Plots showing algorithm convergence to Nash equilibrium

## Project Structure

```
.
├── kuhn_poker.py    # Game implementation (rules, states, actions)
├── cfr.py           # CFR algorithm implementation
├── main.py          # Main script with visualization
└── README.md        # This file
```

## Kuhn Poker Rules

Kuhn Poker is a simplified poker game with:
- **Players**: 2
- **Deck**: 3 cards (Jack < Queen < King)
- **Ante**: Each player puts 1 chip in the pot
- **Actions**: Check, Bet, Fold, Call

### Game Flow

1. Each player is dealt one card (one card unused)
2. **Player 0** acts first:
   - **Check**: Pass action to Player 1
   - **Bet**: Put 1 chip in pot
3. **Player 1** responds:
   - If Player 0 checked: Can check (showdown) or bet
   - If Player 0 bet: Can fold (lose ante) or call (showdown)
4. If Player 1 bets after Player 0 checks, Player 0 can fold or call
5. **Showdown**: Highest card wins the pot

## CFR Algorithm

Counterfactual Regret Minimization learns optimal strategies by:
1. Simulating many game iterations
2. Tracking "regret" for not taking each action
3. Updating strategy to prefer actions with high regret
4. Converging to Nash equilibrium

### Key Components

- **Information Sets**: Represent what a player knows (their card + history)
- **Regret Matching**: Update strategy based on cumulative regrets
- **Reach Probabilities**: Track how likely each state is to be reached

## Usage

### Basic Usage

```python
from kuhn_poker import GameConfig
from cfr import CFRTrainer

# Create configuration
config = GameConfig(ante=1, bet_size=1)

# Initialize trainer
trainer = CFRTrainer(config)

# Train for 10,000 iterations
expected_values = trainer.train(10000)

# Get learned strategies
strategies = trainer.get_strategy_profile()
```

### Running the Complete Analysis

```bash
python main.py
```

This will:
1. Train CFR for 10,000 iterations
2. Print the learned strategy profile
3. Display strategy analysis
4. Save results to `cfr_results.json`
5. Generate convergence plots (`cfr_convergence.png`)

## Configuration Options

### Game Configuration

Modify game rules in `kuhn_poker.py`:

```python
class GameConfig:
    def __init__(self, ante: int = 1, bet_size: int = 1):
        self.ante = ante          # Initial ante amount
        self.bet_size = bet_size  # Size of bets
        self.cards = [Card.JACK, Card.QUEEN, Card.KING]
```

### Training Configuration

Modify training parameters in `main.py`:

```python
config = GameConfig(ante=1, bet_size=1)
num_iterations = 10000  # More iterations = better convergence
```

## Example Output

### Learned Strategies

```
PLAYER 0 STRATEGIES:
  Card: J
    History: (start)
      BET: 0.0000
      CHECK: 1.0000

  Card: K
    History: (start)
      BET: 1.0000
      CHECK: 0.0000
```

This shows that Player 0:
- Always checks with Jack (weakest card)
- Always bets with King (strongest card)

### Convergence

The algorithm converges to the theoretical Nash equilibrium value of **-1/18 ≈ -0.0556** (slight disadvantage for the first player).

## Modifying Game Rules

### Example 1: Change Bet Size

```python
# In main.py
config = GameConfig(ante=1, bet_size=2)  # Larger bets
```

### Example 2: Add More Cards

```python
# In kuhn_poker.py
class GameConfig:
    def __init__(self):
        self.ante = 1
        self.bet_size = 1
        self.cards = [Card.JACK, Card.QUEEN, Card.KING, Card.ACE]
```

### Example 3: Modify Action Space

You can extend `kuhn_poker.py` to add:
- Multiple bet sizes
- Raise actions
- More betting rounds

The tree-based structure makes it easy to add new actions and game states.

## Understanding the Output

### Strategy Profile
- Each information set shows probabilities for each action
- Sum of probabilities = 1.0 for each information set
- Patterns emerge (e.g., always bet with strong cards)

### Convergence Plots
- **Top plot**: Shows per-iteration variance and moving average
- **Bottom plot**: Shows cumulative average converging to Nash value
- Red dashed line: Theoretical optimal value (-1/18)

## Dependencies

```bash
pip install numpy matplotlib
```

## Advanced Usage

### Custom Strategy Evaluation

```python
# Evaluate a specific strategy
trainer = CFRTrainer(config)
trainer.train(10000)

# Access information sets directly
for info_set_key, info_set in trainer.info_sets.items():
    avg_strategy = info_set.get_average_strategy()
    print(f"{info_set_key}: {avg_strategy}")
```

### Comparing Different Configurations

```python
configs = [
    GameConfig(ante=1, bet_size=1),
    GameConfig(ante=1, bet_size=2),
    GameConfig(ante=2, bet_size=1),
]

for config in configs:
    trainer = CFRTrainer(config)
    values = trainer.train(10000)
    print(f"Config {config.ante}/{config.bet_size}: {np.mean(values[-1000:])}")
```

## Theoretical Background

### Nash Equilibrium
Kuhn Poker has a known Nash equilibrium where:
- Expected value: -1/18 for Player 0
- Player 0 should bet with K, check with J, and mix with Q
- Player 1 has corresponding optimal responses

### CFR Convergence
CFR's average strategy converges to Nash equilibrium at a rate of O(1/√T), where T is the number of iterations.

## Future Extensions

Possible modifications:
1. **Multi-round betting**: Allow multiple bet/raise sequences
2. **More players**: Extend to 3+ players
3. **Larger deck**: Use standard 52-card deck with hand rankings
4. **Alternative algorithms**: Implement CFR+, MCCFR, or Deep CFR
5. **External sampling**: More efficient variant of CFR

## References

- Zinkevich et al. (2007): "Regret Minimization in Games with Incomplete Information"
- Kuhn (1950): "A Simplified Two-Person Poker"

## License

MIT License - Free to use and modify for research and education.

