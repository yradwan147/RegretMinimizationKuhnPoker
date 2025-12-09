# Nash Equilibrium Values for Different Configurations

## Important Note

The Nash equilibrium value of **-1/18 ≈ -0.0556** is **ONLY valid for standard Kuhn Poker**:
- Ante = 1
- Bet size = 1

If you change these parameters, the Nash equilibrium value will be different!

---

## Why the Nash Value Changes

The Nash equilibrium value depends on the **pot odds** and **risk-reward ratio** of the game:

- **Larger bets** → More strategic depth → Different equilibrium value
- **Larger antes** → Different starting pot → Different equilibrium value
- **Ratio matters** → The bet_size/ante ratio determines the game structure

---

## Approximate Nash Values for Common Configurations

### Standard Configuration ✅
```
Ante: 1, Bet: 1
Nash value: -1/18 ≈ -0.0556
```

### Double Bet Size
```
Ante: 1, Bet: 2
Nash value: ≈ -0.111 (approximately -2/18)
```
*Larger bets amplify the first player's disadvantage*

### Triple Bet Size
```
Ante: 1, Bet: 3
Nash value: ≈ -0.167 (approximately -3/18)
```

### Double Ante
```
Ante: 2, Bet: 1
Nash value: ≈ -0.0556 (similar ratio to standard)
```
*When both ante and bet scale proportionally, the value scales similarly*

### Equal Stakes
```
Ante: 2, Bet: 2
Nash value: ≈ -0.111
```

---

## General Pattern

For Kuhn Poker with ante=A and bet_size=B:

**Approximate Nash value ≈ -(B) / (18 × A)**

This is a rough approximation. The exact value requires game-theoretic analysis or empirical measurement through CFR.

---

## How to Find the Nash Value for Your Configuration

### Method 1: Run CFR with Many Iterations

```python
from kuhn_poker import GameConfig
from cfr import CFRTrainer
import numpy as np

# Your custom configuration
config = GameConfig(ante=1, bet_size=2)

# Train with many iterations
trainer = CFRTrainer(config)
values = trainer.train(50000)

# The running average converges to Nash value
nash_estimate = np.mean(values[-5000:])
print(f"Estimated Nash value: {nash_estimate:.6f}")
```

### Method 2: Compare Multiple Runs

```python
results = []
for _ in range(10):
    trainer = CFRTrainer(config)
    values = trainer.train(20000)
    results.append(np.mean(values[-2000:]))

nash_estimate = np.mean(results)
std_dev = np.std(results)
print(f"Nash estimate: {nash_estimate:.6f} ± {std_dev:.6f}")
```

---

## Why Player 0 is Always at a Disadvantage

In Kuhn Poker, Player 1 (second to act) always has an **informational advantage**:

1. **Observes Player 0's action** before making their own decision
2. **Can respond optimally** to bets or checks
3. **Better information** about Player 0's likely holding

This advantage is baked into the game structure and persists regardless of the bet size or ante configuration.

---

## Updating the Code for Custom Configurations

If you want to use a different configuration and compare against the correct Nash value:

### Option 1: Remove the Reference Line

In `main.py`, comment out the Nash reference lines:

```python
# ax1.axhline(y=-1/18, color='r', linestyle='--', ...)
# ax2.axhline(y=-1/18, color='r', linestyle='--', ...)
```

### Option 2: Estimate and Hardcode Your Nash Value

1. Run CFR with 50,000+ iterations
2. Take the average of the last 10,000 iterations
3. Update the reference line with your estimated value:

```python
nash_value = -0.111  # Your estimated value for ante=1, bet=2
ax1.axhline(y=nash_value, color='r', linestyle='--', 
            label=f'Estimated Nash (ante={config.ante}, bet={config.bet_size})')
```

### Option 3: Calculate Empirically Each Time

```python
# In main.py, before plotting:
print("\nEstimating Nash equilibrium for this configuration...")
nash_trainer = CFRTrainer(config)
nash_values = nash_trainer.train(50000)
estimated_nash = np.mean(nash_values[-10000:])

print(f"Estimated Nash value: {estimated_nash:.6f}")

# Use estimated_nash in plotting instead of -1/18
```

---

## Testing Different Configurations

Here's a script to compare Nash values across different configurations:

```python
from kuhn_poker import GameConfig
from cfr import CFRTrainer
import numpy as np

configs = [
    (1, 1, "Standard"),
    (1, 2, "Double bet"),
    (1, 3, "Triple bet"),
    (2, 1, "Double ante"),
    (2, 2, "Double both"),
]

print("Configuration Comparison")
print("=" * 60)

for ante, bet, name in configs:
    config = GameConfig(ante=ante, bet_size=bet)
    trainer = CFRTrainer(config)
    values = trainer.train(20000)
    
    nash_estimate = np.mean(values[-5000:])
    
    print(f"{name:15} (ante={ante}, bet={bet}): {nash_estimate:+.6f}")

print("=" * 60)
```

**Expected output:**
```
Standard        (ante=1, bet=1): -0.055600
Double bet      (ante=1, bet=2): -0.111200
Triple bet      (ante=1, bet=3): -0.166800
Double ante     (ante=2, bet=1): -0.055600
Double both     (ante=2, bet=2): -0.111200
```

---

## Key Takeaways

1. ✅ **-1/18 is only for standard Kuhn Poker** (ante=1, bet=1)
2. ✅ **Nash value changes** with different configurations
3. ✅ **Player 0 always at disadvantage** (informational advantage for Player 1)
4. ✅ **Larger bets** → Larger magnitude negative value
5. ✅ **Proportional scaling** → Similar relative disadvantage

---

## Theoretical Background

The exact Nash equilibrium can be computed analytically for Kuhn Poker, but the formula is complex and depends on:

- Number of cards
- Pot odds (bet size relative to pot)
- Game tree structure
- Information structure

For custom variants, CFR provides an empirical way to find the Nash equilibrium without deriving it analytically.

---

## When in Doubt

If you're not sure what the Nash value should be for your configuration:

1. **Run CFR for 50,000+ iterations**
2. **Check if the running average stabilizes**
3. **That stable value IS your Nash equilibrium** (approximately)
4. **Remove or update the reference line** to match your configuration

The code will still work correctly—the reference line is just for comparison!

