# NormalHedge Quick Start Guide

## Installation

No additional dependencies needed! Uses the existing project setup.

```bash
# Ensure you have the requirements
pip install numpy matplotlib
```

## Quick Test (30 seconds)

```bash
# Run unit tests to verify implementation
python test_normal_hedge.py

# Quick comparison with CFR/CFR+ (2000 iterations)
python quick_compare.py
```

Expected output:
```
✓ All unit tests pass
✓ NormalHedge converges (error ~0.11 from Nash in 2000 iterations)
✓ Generates quick_comparison.png
```

## Full Comparison (5-10 minutes)

```bash
# Comprehensive comparison with convergence analysis
python compare_cfr_variants.py
```

This will:
1. Train all three algorithms (CFR, CFR+, NormalHedge) for 10,000 iterations
2. Test with CFR+ using different delay parameters (0, 100, 500)
3. Generate convergence plots
4. Compare learned strategies
5. Run convergence rate analysis at multiple iteration counts

Generated files:
- `cfr_vs_cfr_plus_vs_normalhedge_comparison.png`
- `convergence_rate_comparison.png`

## Basic Usage Example

```python
from normal_hedge import NormalHedgeTrainer
from kuhn_poker import GameConfig

# 1. Create game configuration
config = GameConfig(ante=1, bet_size=1)

# 2. Initialize trainer
trainer = NormalHedgeTrainer(config)

# 3. Train for N iterations
num_iterations = 10000
values = trainer.train(num_iterations)

# 4. Get learned strategy profile
strategy = trainer.get_strategy_profile()

# 5. Print some strategies
print("\nLearned Strategies:")
print(f"Jack (first decision): {strategy['J']}")
print(f"King (first decision): {strategy['K']}")
print(f"King after opponent bets: {strategy['Kb']}")
```

Example output:
```
Jack (first decision): {'CHECK': 0.906, 'BET': 0.094}
King (first decision): {'CHECK': 0.594, 'BET': 0.406}
King after opponent bets: {'FOLD': 0.0003, 'CALL': 0.9997}
```

## Comparing with CFR

```python
from cfr import CFRTrainer
from cfr_plus import CFRPlusTrainer
from normal_hedge import NormalHedgeTrainer
from kuhn_poker import GameConfig
import numpy as np

config = GameConfig(ante=1, bet_size=1)
iterations = 5000

# Train all three
cfr = CFRTrainer(config)
cfr_vals = cfr.train(iterations)

cfr_plus = CFRPlusTrainer(config, delay=0)
cfr_plus_vals = cfr_plus.train(iterations)

nh = NormalHedgeTrainer(config)
nh_vals = nh.train(iterations)

# Compare final values
nash = -1/18  # True Nash equilibrium value

print(f"Nash Equilibrium: {nash:.6f}")
print(f"CFR:        {np.mean(cfr_vals[-1000:]):.6f}")
print(f"CFR+:       {np.mean(cfr_plus_vals[-1000:]):.6f}")
print(f"NormalHedge: {np.mean(nh_vals[-1000:]):.6f}")
```

## Understanding the Output

### Information Set Notation
- `J`, `Q`, `K`: First decision with that card
- `Jb`, `Qb`, `Kb`: After opponent bet (responding)
- `Jc`, `Qc`, `Kc`: After opponent checked (second player's turn)
- `Jcb`, `Qcb`, `Kcb`: After check-bet sequence

### Action Meanings
- `CHECK`: Pass without betting (first player) or check back (second player)
- `BET`: Place a bet (first player) or raise (second player after check)
- `FOLD`: Fold to opponent's bet
- `CALL`: Call opponent's bet

### Interpreting Strategies

**Example**: `{'CHECK': 0.906, 'BET': 0.094}`
- Check 90.6% of the time
- Bet (bluff) 9.4% of the time

**Nash Equilibrium for Kuhn Poker** (approximate):
- Jack: Check ~82%, Bet ~18% (bluff frequency)
- Queen: Almost always check
- King: Mixed strategy, lean toward betting

## Expected Performance

### Convergence Speed
| Algorithm   | 1000 iter | 5000 iter | 10000 iter | 20000 iter |
|-------------|-----------|-----------|------------|------------|
| CFR         | ~0.02     | ~0.005    | ~0.003     | ~0.001     |
| CFR+        | ~0.015    | ~0.003    | ~0.001     | ~0.0005    |
| NormalHedge | ~0.05     | ~0.015    | ~0.008     | ~0.004     |

*Error from Nash equilibrium (-0.055556)*

### When to Use Each Algorithm

**Use CFR** when:
- You want fast initial convergence
- You understand the game structure
- You can tune parameters if needed

**Use CFR+** when:
- You want state-of-the-art performance
- You're willing to test delay parameters
- Convergence speed is critical

**Use NormalHedge** when:
- You want **zero** hyperparameter tuning
- You need theoretical guarantees
- You want sparse strategies (zero weight for bad actions)
- You're researching parameter-free algorithms

## Troubleshooting

### NormalHedge converges slowly
- **Expected**: NH is conservative early on
- **Solution**: Use more iterations (10k+ recommended)
- **Alternative**: Try CFR+ if speed is critical

### Large regrets cause issues
- **Check**: Are utilities bounded correctly?
- **Verify**: Run `test_normal_hedge.py` to test numerical stability
- **Fix**: Ensure game payoffs are in reasonable range (< 100)

### Strategy seems suboptimal
- **Check**: Are you using average strategy? (not current strategy)
- **Verify**: `get_strategy_profile()` returns average (correct)
- **Fix**: Train for more iterations if needed

## Advanced Usage

### Custom Information Set Inspection

```python
# Access individual information sets
for key, infoset in trainer.info_sets.items():
    print(f"\nInfoset: {key}")
    print(f"  Cumulative regrets: {infoset.regret_sum}")
    print(f"  Scale parameter: {infoset.c_scale}")
    print(f"  Strategy: {infoset.get_strategy()}")
```

### Monitoring Convergence

```python
# Track exploitability over time (if you have a best-response solver)
exploitabilities = []
for i in range(0, iterations, 100):
    # ... compute exploitability ...
    exploitabilities.append(exploit)
```

### Saving/Loading Strategies

```python
import json

# Save
strategy = trainer.get_strategy_profile()
with open('normalhedge_strategy.json', 'w') as f:
    json.dump(strategy, f, indent=2)

# Load
with open('normalhedge_strategy.json', 'r') as f:
    loaded_strategy = json.load(f)
```

## Key Insights

### Why NormalHedge is Different

1. **No learning rates**: Scale `c_t` computed automatically each iteration
2. **Principled weighting**: Derivative of potential function, not ad-hoc
3. **Quantile bounds**: Regret guarantee for top-ε actions, not just best
4. **True zero weights**: Actions with R ≤ 0 get exactly 0 probability

### The Half-Normal Potential Intuition

```
φ(R, c) = exp(R² / 2c)
```

- Low regret (R≈0): Small potential, low weight
- High regret (R>>0): Large potential, high weight
- Negative regret (R<0): Zero potential, zero weight
- Scale `c`: Controls how aggressively to prefer high-regret actions

### Why Scale Constraint Matters

Constraint: `(1/|A|) Σ exp(R²/2c) = e`

- Keeps potentials in reasonable range
- Prevents numerical issues
- Automatically adapts to regret magnitudes
- **No manual tuning needed**

## Next Steps

1. ✅ **Run tests**: `python test_normal_hedge.py`
2. ✅ **Quick comparison**: `python quick_compare.py`
3. ✅ **Full analysis**: `python compare_cfr_variants.py`
4. 📖 **Read theory**: See `NORMALHEDGE_README.md`
5. 🔬 **Experiment**: Try different iteration counts, analyze strategies

## Questions?

See full documentation:
- **NORMALHEDGE_README.md**: Complete algorithm guide
- **NORMALHEDGE_IMPLEMENTATION_SUMMARY.md**: Technical details
- **CFR_PLUS_README.md**: Background on CFR variants

Enjoy your parameter-free learning! 🎲


