# Customization Guide for Kuhn Poker CFR

This guide shows you how to modify the game rules and experiment with different configurations.

## Quick Start Examples

### 1. Change Bet Size

```python
from kuhn_poker import GameConfig
from cfr import CFRTrainer

# Create config with larger bet size
config = GameConfig(ante=1, bet_size=3)
trainer = CFRTrainer(config)
trainer.train(10000)
```

### 2. Different Ante Values

```python
# Higher stakes game
config = GameConfig(ante=5, bet_size=5)
trainer = CFRTrainer(config)
trainer.train(10000)
```

### 3. Run Multiple Experiments

```python
import numpy as np

configs = [
    GameConfig(ante=1, bet_size=1),
    GameConfig(ante=1, bet_size=2),
    GameConfig(ante=2, bet_size=1),
]

results = {}
for i, config in enumerate(configs):
    trainer = CFRTrainer(config)
    values = trainer.train(5000)
    results[f'config_{i}'] = np.mean(values[-500:])
    print(f"Config {i}: Final value = {results[f'config_{i}']:.4f}")
```

## Advanced Modifications

### Adding More Cards

To add a 4-card variant (e.g., Jack, Queen, King, Ace):

**Step 1**: Modify `kuhn_poker.py` - Add new card:

```python
class Card(Enum):
    """Card values in Kuhn Poker"""
    JACK = 0
    QUEEN = 1
    KING = 2
    ACE = 3  # Add new card
    
    def __lt__(self, other):
        return self.value < other.value
```

**Step 2**: Update GameConfig:

```python
class GameConfig:
    def __init__(self, ante: int = 1, bet_size: int = 1):
        self.ante = ante
        self.bet_size = bet_size
        self.cards = [Card.JACK, Card.QUEEN, Card.KING, Card.ACE]  # 4 cards
```

**Step 3**: Update game state to handle 2 out of 4 cards (no changes needed - already handles this!)

**Step 4**: Run training:

```python
config = GameConfig()
trainer = CFRTrainer(config)
trainer.train(20000)  # May need more iterations with more cards
```

### Adding Multiple Bet Sizes

To allow small and large bets:

**Step 1**: Extend Action enum in `kuhn_poker.py`:

```python
class Action(Enum):
    """Possible actions in Kuhn Poker"""
    CHECK = 0
    BET_SMALL = 1
    BET_LARGE = 2
    FOLD = 3
    CALL = 4
```

**Step 2**: Update GameConfig:

```python
class GameConfig:
    def __init__(self, ante: int = 1, small_bet: int = 1, large_bet: int = 2):
        self.ante = ante
        self.small_bet = small_bet
        self.large_bet = large_bet
        self.cards = [Card.JACK, Card.QUEEN, Card.KING]
```

**Step 3**: Modify `get_legal_actions()` in `kuhn_poker.py`:

```python
def get_legal_actions(self) -> List[Action]:
    """Get legal actions for the current state"""
    if self.is_terminal():
        return []
    
    if len(self.history) == 0:
        # First action: Can check or bet (small or large)
        return [Action.CHECK, Action.BET_SMALL, Action.BET_LARGE]
    
    # ... handle other cases
```

**Step 4**: Update terminal states and payoffs accordingly

**Step 5**: Update `_action_to_char()` to handle new actions:

```python
@staticmethod
def _action_to_char(action: Action) -> str:
    """Convert action to character for history string"""
    if action == Action.CHECK:
        return 'c'
    elif action == Action.BET_SMALL:
        return 's'  # small bet
    elif action == Action.BET_LARGE:
        return 'b'  # large bet
    elif action == Action.FOLD:
        return 'f'
    elif action == Action.CALL:
        return 'c'
    return ''
```

### Adding More Betting Rounds

To allow re-raises (more complex):

**Step 1**: Modify `is_terminal()` to handle longer histories:

```python
def is_terminal(self) -> bool:
    """Check if the game state is terminal"""
    # Max 3 betting rounds
    if self.history.count('b') >= 3:
        return True
    
    # Fold endings
    if self.history.endswith('f'):
        return True
    
    # Both checked twice in a row
    if self.history.endswith('cc'):
        return True
    
    # Called after bet
    if len(self.history) >= 2 and self.history[-1] == 'c' and self.history[-2] == 'b':
        return True
    
    return False
```

**Step 2**: Update `get_legal_actions()` to allow raises

**Step 3**: Update payoff calculations to account for total pot size

### Changing to 3 Players

This requires more substantial changes:

**Step 1**: Modify GameState to track 3 players:

```python
class GameState:
    def __init__(self, config: GameConfig, cards: List[Card], history: str = "", active_players: List[bool] = None):
        self.config = config
        self.cards = cards  # cards[0], cards[1], cards[2] for 3 players
        self.history = history
        self.pot = 3 * config.ante  # All three ante
        self.active_players = active_players or [True, True, True]
```

**Step 2**: Update `get_current_player()` to rotate through 3 players

**Step 3**: Update terminal conditions and payoff calculations

**Step 4**: Update CFR algorithm to handle 3-player game tree

### Custom Strategy Initialization

To start with a specific strategy (instead of uniform):

**Step 1**: Modify `InformationSet` in `cfr.py`:

```python
class InformationSet:
    def __init__(self, num_actions: int, initial_strategy: np.ndarray = None):
        self.num_actions = num_actions
        self.regret_sum = np.zeros(num_actions)
        self.strategy_sum = np.zeros(num_actions)
        
        if initial_strategy is not None:
            self.strategy = initial_strategy
        else:
            self.strategy = np.ones(num_actions) / num_actions
```

**Step 2**: Use custom initialization:

```python
# Example: Always bet initially
trainer = CFRTrainer(config)

# Manually set initial strategies
for card in ['J', 'Q', 'K']:
    info_set_key = f"{card}"
    info_set = trainer.get_info_set(info_set_key, 2)
    info_set.strategy = np.array([0.0, 1.0])  # Always bet

trainer.train(10000)
```

## Performance Tuning

### Faster Training

```python
# Use fewer iterations for quick tests
trainer.train(1000)

# Use more iterations for accurate results
trainer.train(50000)
```

### Memory Optimization

For larger games, you might want to implement:

1. **External Sampling CFR**: Only sample a subset of actions
2. **Monte Carlo CFR**: Sample chance outcomes instead of exact computation
3. **CFR+**: Improved regret updates for faster convergence

### Parallelization

To run multiple experiments in parallel:

```python
from multiprocessing import Pool

def train_config(config_tuple):
    ante, bet_size = config_tuple
    config = GameConfig(ante=ante, bet_size=bet_size)
    trainer = CFRTrainer(config)
    values = trainer.train(5000)
    return (ante, bet_size, np.mean(values[-500:]))

if __name__ == "__main__":
    configs = [(1, 1), (1, 2), (2, 1), (2, 2)]
    
    with Pool(4) as p:
        results = p.map(train_config, configs)
    
    for ante, bet, value in results:
        print(f"Ante={ante}, Bet={bet}: {value:.4f}")
```

## Visualization Customization

### Custom Plots

```python
import matplotlib.pyplot as plt
import numpy as np

# Train
trainer = CFRTrainer(config)
values = trainer.train(10000)

# Custom plot
plt.figure(figsize=(12, 6))
plt.plot(values, alpha=0.5, linewidth=0.5)
plt.xlabel('Iteration')
plt.ylabel('Expected Value')
plt.title('My Custom CFR Convergence Plot')
plt.grid(True)
plt.savefig('my_plot.png')
```

### Strategy Heatmaps

```python
import matplotlib.pyplot as plt
import numpy as np

# Get strategies
profile = trainer.get_strategy_profile()

# Create heatmap data
cards = ['J', 'Q', 'K']
actions = ['CHECK', 'BET']
data = np.zeros((3, 2))

for i, card in enumerate(cards):
    if card in profile:
        data[i, 0] = profile[card]['CHECK']
        data[i, 1] = profile[card]['BET']

# Plot heatmap
fig, ax = plt.subplots(figsize=(6, 4))
im = ax.imshow(data, cmap='YlOrRd')

ax.set_xticks(np.arange(len(actions)))
ax.set_yticks(np.arange(len(cards)))
ax.set_xticklabels(actions)
ax.set_yticklabels(cards)

# Add text annotations
for i in range(len(cards)):
    for j in range(len(actions)):
        text = ax.text(j, i, f'{data[i, j]:.2f}',
                      ha="center", va="center", color="black")

ax.set_title("Initial Action Strategy Heatmap")
fig.tight_layout()
plt.savefig('strategy_heatmap.png')
```

## Testing and Validation

### Unit Tests

Create `test_kuhn_poker.py`:

```python
import unittest
from kuhn_poker import GameConfig, GameState, Card, Action

class TestKuhnPoker(unittest.TestCase):
    def setUp(self):
        self.config = GameConfig(ante=1, bet_size=1)
    
    def test_terminal_state_both_check(self):
        cards = [Card.KING, Card.QUEEN]
        state = GameState(self.config, cards, history="cc")
        self.assertTrue(state.is_terminal())
    
    def test_payoff_higher_card_wins(self):
        cards = [Card.KING, Card.QUEEN]
        state = GameState(self.config, cards, history="cc")
        self.assertEqual(state.get_payoff(0), 1)  # Player 0 wins ante
        self.assertEqual(state.get_payoff(1), -1)
    
    def test_legal_actions_start(self):
        cards = [Card.KING, Card.QUEEN]
        state = GameState(self.config, cards, history="")
        actions = state.get_legal_actions()
        self.assertEqual(len(actions), 2)
        self.assertIn(Action.CHECK, actions)
        self.assertIn(Action.BET, actions)

if __name__ == '__main__':
    unittest.main()
```

### Validate Nash Equilibrium

```python
from cfr import CFRTrainer
from kuhn_poker import GameConfig

config = GameConfig(ante=1, bet_size=1)
trainer = CFRTrainer(config)
trainer.train(50000)  # High number for accuracy

# Calculate expected value
values = []
for _ in range(1000):
    deck = config.get_deck()
    cards = [deck[0], deck[1]]
    from kuhn_poker import GameState
    state = GameState(config, cards)
    value = trainer.cfr(state, 1.0, 1.0)
    values.append(value)

avg_value = np.mean(values)
print(f"Average value: {avg_value:.6f}")
print(f"Theoretical Nash: {-1/18:.6f}")
print(f"Error: {abs(avg_value - (-1/18)):.6f}")
```

## Common Issues and Solutions

### Issue: Strategies not converging

**Solution**: Increase number of iterations (try 20000+)

### Issue: Memory usage too high

**Solution**: Implement external sampling CFR or clear strategy sums periodically

### Issue: Slow training

**Solution**: Use PyPy instead of CPython, or implement in Cython/Numba

### Issue: Different results each run

**Solution**: Set random seed:
```python
import random
random.seed(42)
np.random.seed(42)
```

## Further Reading

- Original CFR paper: Zinkevich et al. (2007)
- CFR+ paper: Tammelin (2014)
- Deep CFR: Brown et al. (2019)
- Libratus/Pluribus poker AIs (use CFR variants)

