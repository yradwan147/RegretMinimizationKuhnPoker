# Implementation Notes: CFR for Kuhn Poker

## Overview

This is a **tree-based** implementation of Counterfactual Regret Minimization (CFR) for Kuhn Poker. Unlike hashmap-based implementations, this uses explicit game tree traversal for clarity and extensibility.

## Key Design Decisions

### 1. Tree-Based Structure

**Why:** Makes it easy to modify game rules and understand the algorithm flow.

```
Game Tree Structure:
    Root
    ├── Player 0 acts (card J/Q/K)
    │   ├── Check → Player 1 acts
    │   │   ├── Check → Terminal (showdown)
    │   │   └── Bet → Player 0 acts
    │   │       ├── Fold → Terminal
    │   │       └── Call → Terminal (showdown)
    │   └── Bet → Player 1 acts
    │       ├── Fold → Terminal
    │       └── Call → Terminal (showdown)
```

### 2. Information Sets

Information sets are identified by:
- Player's card (J, Q, or K)
- Action history (empty, "b", "c", "cb", etc.)

Examples:
- `"K"`: Player has King, no actions yet
- `"Jb"`: Player has Jack, opponent bet
- `"Qcb"`: Player has Queen, player checked, opponent bet

### 3. Action Representation

Actions are represented as enums for type safety:
```python
Action.CHECK  # Pass action to opponent
Action.BET    # Add bet_size chips to pot
Action.FOLD   # Give up (only after opponent bets)
Action.CALL   # Match opponent's bet
```

History is stored as a string for compact representation:
- 'c' = check
- 'b' = bet
- 'f' = fold
- 'c' = call (context determines which)

### 4. CFR Algorithm Flow

```python
def cfr(state, reach_prob_0, reach_prob_1):
    if terminal:
        return payoff
    
    # Get information set
    info_set = get_or_create(state.get_info_set())
    strategy = info_set.get_strategy()  # From regret matching
    
    # Calculate utilities for each action
    for action in legal_actions:
        next_state = state.apply_action(action)
        utility[action] = cfr(next_state, ...)
    
    # Update regrets
    for action in legal_actions:
        regret[action] = utility[action] - expected_utility
        info_set.add_regret(regret[action])
    
    # Update strategy sum for averaging
    info_set.update_strategy_sum()
    
    return expected_utility
```

### 5. Regret Matching

At each information set:
1. Track cumulative regret for each action
2. Compute strategy proportional to **positive** regrets
3. If no positive regrets, use uniform strategy

```python
def get_strategy():
    positive_regrets = max(regret_sum, 0)
    if sum(positive_regrets) > 0:
        strategy = positive_regrets / sum(positive_regrets)
    else:
        strategy = uniform
    return strategy
```

### 6. Average Strategy

The **average strategy** (not the current strategy) converges to Nash equilibrium:

```python
# Each iteration
info_set.strategy_sum += reach_probability * current_strategy

# At the end
average_strategy = strategy_sum / sum(strategy_sum)
```

## Code Architecture

### `kuhn_poker.py`
- **GameConfig**: Configurable game rules (ante, bet size, cards)
- **GameState**: Represents a point in the game tree
  - `is_terminal()`: Check if game is over
  - `get_payoff()`: Return payoff at terminal states
  - `get_legal_actions()`: Return available actions
  - `apply_action()`: Create new state after action
  - `get_info_set()`: Get information set identifier
- **Card/Action**: Enums for type safety

### `cfr.py`
- **InformationSet**: Tracks regrets and strategies
  - `regret_sum`: Cumulative regrets
  - `strategy_sum`: Cumulative strategies (for averaging)
  - `get_strategy()`: Regret matching
  - `get_average_strategy()`: Final strategy
- **CFRTrainer**: Main algorithm
  - `train()`: Run iterations
  - `cfr()`: Recursive tree traversal
  - `get_strategy_profile()`: Extract learned strategies

### `main.py`
- Training loop
- Strategy visualization
- Convergence plotting
- Results export

### `experiment.py`
- Comparative experiments
- Different configurations
- Multiple visualizations

### `interactive_play.py`
- Play against the trained AI
- Human vs CFR strategy

## Algorithm Complexity

### Time Complexity
- **Per iteration**: O(|I| × |A|) where I = information sets, A = actions
- **For Kuhn Poker**: O(12 × 2) = O(24) per iteration (very fast!)
- **Full training**: O(T × 24) for T iterations

### Space Complexity
- **O(|I| × |A|)** to store regret sums and strategy sums
- **For Kuhn Poker**: O(12 × 2) = O(24) (minimal memory!)

### Convergence Rate
- CFR converges at rate **O(1/√T)** to Nash equilibrium
- Practically: 10,000 iterations usually sufficient for Kuhn Poker

## Theoretical Results for Kuhn Poker

### Nash Equilibrium Value
- **-1/18 ≈ -0.0556** for first player (slight disadvantage)
- This is the expected value when both players play optimally

### Optimal Strategies (Approximate)

**Player 0 (first to act):**
- Jack: Always check, fold to bet
- Queen: Check, call with ~1/3 probability if bet
- King: Bet with ~3/4 probability

**Player 1 (second to act):**
- Jack: Check if checked to, fold to bet
- Queen: Check if checked to, call ~1/3 of bets
- King: Bet if checked to, call all bets

## Verification

The implementation can be verified by:

1. **Checking convergence**: Final value should approach -1/18
2. **Inspecting strategies**: Should match known optimal strategies
3. **Exploitability**: Computing best response value

## Extensions and Modifications

### Easy Extensions
1. **Change bet sizes**: Modify `GameConfig`
2. **Add cards**: Extend `Card` enum and `GameConfig.cards`
3. **Different antes**: Change `GameConfig.ante`

### Medium Extensions
1. **Multiple bet sizes**: Add actions for different bet amounts
2. **More betting rounds**: Allow raises and re-raises
3. **Chance sampling**: Sample cards instead of exact traversal

### Hard Extensions
1. **3+ players**: Requires rewriting payoff logic
2. **Larger games**: Need more efficient variants (CFR+, MCCFR)
3. **Imperfect recall**: More complex information sets

## Performance Tips

### For Faster Training
1. Use PyPy: `pypy3 main.py` (can be 3-5x faster)
2. Implement in Cython or Numba
3. Use CFR+ variant (better convergence)
4. External sampling (sample actions)

### For Larger Games
1. **Monte Carlo CFR**: Sample chance outcomes
2. **Pruning**: Skip low-probability branches
3. **Abstraction**: Group similar states together
4. **Deep CFR**: Use neural networks for value functions

## Common Pitfalls

### 1. Using Current Strategy Instead of Average
❌ Wrong: `info_set.strategy`
✅ Correct: `info_set.get_average_strategy()`

The current strategy fluctuates; only the average converges!

### 2. Forgetting Reach Probabilities
Regret updates must be weighted by opponent's reach probability:
```python
regret += opponent_reach_prob * (action_value - expected_value)
```

### 3. Not Updating Strategy Sum
Must accumulate strategy sum weighted by player's reach probability:
```python
strategy_sum += player_reach_prob * current_strategy
```

### 4. Terminal State Payoffs
Payoffs must be from player 0's perspective throughout the algorithm.

## Testing Checklist

- [ ] Terminal states return correct payoffs
- [ ] Legal actions match game rules
- [ ] Information sets correctly identify game state
- [ ] Regret updates weighted by reach probabilities
- [ ] Strategy sum accumulated correctly
- [ ] Average strategy converges to theoretical value
- [ ] Strategies make intuitive sense (bet with strong cards, etc.)

## Debugging Tips

### 1. Print Information Sets
```python
for key, info_set in trainer.info_sets.items():
    print(f"{key}: {info_set.get_average_strategy()}")
```

### 2. Track Specific Information Set
```python
def cfr(...):
    if state.get_info_set(player) == "K":  # Track King at start
        print(f"Iteration {self.iteration}: strategy = {strategy}")
```

### 3. Verify Payoffs
```python
# Test all terminal states manually
test_cases = [
    ("cc", Card.KING, Card.QUEEN, 1),   # King wins after both check
    ("bf", Card.JACK, Card.QUEEN, 1),   # Jack bets, Queen folds
    # ... more cases
]
```

### 4. Check Regret Growth
Regrets should not grow unboundedly:
```python
max_regret = max(abs(r) for info_set in trainer.info_sets.values() 
                 for r in info_set.regret_sum)
print(f"Max regret: {max_regret}")
```

## Resources

### Papers
1. **Zinkevich et al. (2007)**: "Regret Minimization in Games with Incomplete Information"
   - Original CFR paper
2. **Bowling et al. (2015)**: "Heads-up Limit Hold'em Poker is Solved"
   - CFR+ and other improvements
3. **Brown & Sandholm (2017)**: "Safe and Nested Subgame Solving"
   - Advanced techniques

### Implementations
- OpenSpiel (Google DeepMind): `python -m open_spiel.python.examples.cfr`
- PokerRL: Research-grade poker RL library
- This implementation: Educational tree-based approach

### Books
- "The Mathematics of Poker" by Chen & Ankenman
- "Artificial Intelligence: A Modern Approach" (4th ed.) - Chapter on game theory

## Acknowledgments

Based on the original CFR algorithm by Zinkevich et al. (2007) and Kuhn's original poker variant (1950).

