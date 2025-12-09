# NormalHedge+ Implementation

## Overview

NormalHedge+ is a modification of the NormalHedge algorithm that incorporates **Regret Matching+ (RM+) truncation** from the CFR+ algorithm. This implementation is designed to test whether the RM+ truncation structure provides similar performance improvements in the parameter-free NormalHedge framework as it does in CFR/CFR+.

## Key Innovation

The critical modification is in the regret update step:

**NormalHedge (Original):**
```
R_{i,t} = R_{i,t-1} + r_{i,t}
```

**NormalHedge+ (With RM+ Truncation):**
```
R'_{i,t} = max{R'_{i,t-1} + r_{i,t}, 0}
```

This ensures cumulative regrets never fall below zero, allowing the algorithm to "forget" periods of poor performance and adapt faster when actions start performing well again.

## Implementation Files

### Core Algorithm
- **`normal_hedge_plus.py`** - Complete implementation of NormalHedge+ algorithm
  - `InformationSetNHPlus` class with RM+ truncated regret updates
  - `NormalHedgePlusTrainer` class for Kuhn Poker training

### Comparison Scripts
Both comparison scripts have been updated to include NormalHedge+:

- **`compare_cfr_variants.py`** - Comprehensive comparison of all four algorithms:
  - CFR (vanilla)
  - CFR+ (with different delay parameters)
  - NormalHedge
  - NormalHedge+

- **`quick_compare.py`** - Fast comparison for testing (2000 iterations by default)

### Testing
- **`test_normal_hedge_plus.py`** - Verification tests demonstrating:
  - Basic functionality of NormalHedge+
  - RM+ truncation mechanism
  - Comparison of regret accumulation vs truncation

## Algorithm Specification

### Parameters and Variables

| Variable | Description | Initial Value |
|----------|-------------|---------------|
| N | Total number of actions | Fixed |
| T | Total number of rounds | Fixed |
| ℓ_{i,t} | Loss for action i in round t | Observed |
| p_{i,t} | Probability weight for action i at round t | 1/N |
| r_{i,t} | Instantaneous regret for action i | Calculated |
| **R'_{i,t}** | **Truncated cumulative regret (RM+)** | **0** |
| c_t | Adaptive scale parameter | Line search |

### Key Steps (Per Round)

1. **Observe losses** and calculate learner's expected loss
2. **Calculate instantaneous regret**: r_{i,t} = ℓ_{A,t} - ℓ_{i,t}
3. **Update with RM+ truncation**: R'_{i,t} = max{R'_{i,t-1} + r_{i,t}, 0}
4. **Solve for scale parameter** c_t via line search: (1/N) Σ exp(R'_{i,t}² / 2c_t) = e
5. **Compute weights**: w_{i,t+1} ∝ (R'_{i,t} / c_t) · exp(R'_{i,t}² / 2c_t)
6. **Normalize** to get probability distribution

## Expected Benefits

Based on the success of RM+ in CFR:

1. **Faster Convergence**: Similar to CFR+ vs CFR, expect order-of-magnitude speedup
2. **Better Adaptation**: Faster recovery when previously-poor actions start performing well
3. **No Negative Ballast**: Actions aren't penalized indefinitely for past poor performance

## Running Comparisons

### Quick Test (2000 iterations)
```bash
python quick_compare.py
```

### Full Comparison (10000 iterations)
```bash
python compare_cfr_variants.py
```

### Run Tests
```bash
python test_normal_hedge_plus.py
```

## Results Interpretation

The comparison scripts generate:

1. **Convergence plots** showing running averages for all algorithms
2. **Error plots** showing convergence speed (log scale)
3. **Strategy comparisons** for key information sets
4. **Performance metrics**:
   - Final game value
   - Error from Nash equilibrium
   - Training time
   - Speedup comparisons

### Key Metrics to Watch

- **Convergence Rate**: Does NormalHedge+ converge faster than NormalHedge?
- **Final Accuracy**: Do all algorithms reach similar final strategies?
- **Computational Efficiency**: Is there a speedup similar to CFR+ vs CFR?

## Mathematical Foundation

### Potential Function
Both NormalHedge and NormalHedge+ use the half-normal potential:

```
φ(x, c) = exp((max{x,0}²) / (2c))
```

Since R'_{i,t} ≥ 0 in NormalHedge+, the max operator is redundant:

```
φ(R'_{i,t}, c) = exp((R'_{i,t})² / (2c))
```

### Scale Parameter Constraint
The scale parameter c_t is found by solving:

```
(1/N) Σ_{i=1}^N exp((R'_{i,t})² / (2c_t)) = e
```

This is done via bisection search (60 iterations for convergence).

### Weight Update Formula
The probability weight for action i is:

```
p_{i,t+1} ∝ (R'_{i,t} / c_t) · exp((R'_{i,t})² / (2c_t))
```

Normalized to ensure Σ p_{i,t+1} = 1.

## Comparison with Other Algorithms

| Algorithm | Regret Update | Parameters | Key Feature |
|-----------|---------------|------------|-------------|
| CFR | R += regret | None | Standard regret matching |
| CFR+ | R = max(R + regret, 0) | delay | RM+ truncation |
| NormalHedge | R += regret | None | Parameter-free, half-normal potential |
| **NormalHedge+** | **R = max(R + regret, 0)** | **None** | **RM+ + parameter-free** |

## Code Structure

### InformationSetNHPlus Class

Key methods:
- `normalhedge_weight()` - Compute unnormalized weights
- `solve_c_scale()` - Find scale parameter via line search
- `get_strategy()` - Compute current strategy
- `add_regret()` - **Update regrets with RM+ truncation** (key modification)
- `get_average_strategy()` - Compute time-averaged strategy

### NormalHedgePlusTrainer Class

Key methods:
- `train()` - Main training loop
- `normalhedge_plus_cfr()` - Recursive CFR with NormalHedge+ updates
- `get_strategy_profile()` - Extract learned strategies

## References

1. **NormalHedge**: Chaudhuri, Freund, Hsu - "A Parameter-free Hedging Algorithm"
2. **CFR+**: Brown & Sandholm - "Solving Imperfect Information Games Using Decomposition"
3. **Regret Matching+**: The truncation R'_t = max{R_{t-1} + r_t, 0}

## Future Extensions

Potential improvements to explore:

1. **Linear Averaging**: Incorporate linear averaging like CFR+
2. **Alternating Updates**: Update only current player's regrets
3. **Discounting**: Add discounting to older regrets
4. **Adaptive Truncation**: Experiment with different truncation thresholds

## Notes

- The RM+ truncation is a **structural modification**, not a hyperparameter
- Unlike CFR+, NormalHedge+ has **no delay parameter** (fully parameter-free)
- The scale parameter c_t is **computed automatically** via line search
- Actions with R'_{i,t} = 0 receive **zero weight** in the strategy

---

For questions or issues, refer to the test file `test_normal_hedge_plus.py` for detailed examples of the truncation mechanism.

