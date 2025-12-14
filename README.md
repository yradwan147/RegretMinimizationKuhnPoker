# Regret Minimization Algorithms for Kuhn Poker

A comprehensive implementation and comparison of four regret minimization algorithms applied to Kuhn Poker, a minimal yet strategically rich imperfect-information game.

## 🎯 Overview

This project implements and compares:

| Algorithm | Description | Key Feature |
|-----------|-------------|-------------|
| **CFR** | Counterfactual Regret Minimization | Foundational algorithm, O(1/√T) convergence |
| **CFR+** | CFR with Regret Matching+ | RM+ truncation, O(1/T) convergence |
| **NormalHedge** | Parameter-free potential-based method | Exponential weighting, automatic adaptation |
| **NormalHedge+** | Novel hybrid (our contribution) | Combines NormalHedge + RM+ truncation |

### Key Features

- 🎮 **Tree-based game implementation**: Clean, extensible Kuhn Poker engine
- 🔬 **Four algorithm implementations**: CFR, CFR+, NormalHedge, NormalHedge+
- 📊 **Comprehensive experiments**: Multiple game configurations and iteration budgets
- 📈 **Strategy convergence analysis**: Compare learned strategies to Nash equilibrium
- 📄 **Full academic report**: NeurIPS-format LaTeX document with detailed analysis

## 📁 Project Structure

```
.
├── kuhn_poker.py                    # Game implementation (rules, states, actions)
├── cfr.py                           # CFR algorithm implementation
├── cfr_plus.py                      # CFR+ algorithm implementation
├── normal_hedge.py                  # NormalHedge algorithm implementation
├── normal_hedge_plus.py             # NormalHedge+ algorithm implementation
├── main.py                          # Basic CFR demo script
├── compare_cfr_variants.py          # Compare CFR vs CFR+
├── comprehensive_experiments.py     # Full experimental suite (all 4 algorithms)
├── strategy_analysis.py             # Strategy convergence analysis
├── quick_compare.py                 # Fast comparison script
├── interactive_play.py              # Play against trained AI
├── finalreport.tex                  # Full academic report (NeurIPS format)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🃏 Kuhn Poker

Kuhn Poker is the simplest poker variant that retains essential strategic elements:

- **Players**: 2
- **Deck**: 3 cards (Jack < Queen < King)
- **Ante**: Each player puts 1 chip in the pot
- **Actions**: Check, Bet, Fold, Call

### Game Flow

```
1. Deal cards → Player 0 gets one, Player 1 gets one
2. Player 0: CHECK or BET
3. Player 1: 
   - After CHECK: CHECK (showdown) or BET
   - After BET: FOLD or CALL (showdown)
4. If Player 1 bets after check: Player 0 can FOLD or CALL
5. Showdown: Higher card wins
```

### Nash Equilibrium

- **Expected value**: -1/18 ≈ -0.0556 for Player 0
- **Jack bluffing**: Bet with probability 1/3
- **Queen**: Always check
- **King**: Bet with probability ≥ 2/3

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Comprehensive Experiments

```bash
python comprehensive_experiments.py
```

This runs all four algorithms across multiple configurations and generates:
- Convergence plots
- Error comparison charts
- Training time analysis
- Comprehensive summary figure

### Run Strategy Convergence Analysis

```bash
python strategy_analysis.py
```

Analyzes how learned strategies converge to Nash equilibrium across iterations.

### Quick Comparison

```bash
python quick_compare.py
```

Fast comparison with fewer iterations for testing.

## 📊 Algorithms

### CFR (Counterfactual Regret Minimization)

The foundational algorithm for solving imperfect-information games.

```python
from cfr import CFRTrainer
from kuhn_poker import GameConfig

config = GameConfig(ante=1, bet_size=1)
trainer = CFRTrainer(config)
values = trainer.train(10000)
strategies = trainer.get_strategy_profile()
```

**Key equations:**
- Strategy: σ(a) = R⁺(a) / Σ R⁺(a')
- Regret update: R(a) = R(a) + π₋ᵢ × (v(a) - v̄)
- Convergence: O(1/√T)

### CFR+ (CFR with Regret Matching+)

Improved variant with faster convergence.

```python
from cfr_plus import CFRPlusTrainer

trainer = CFRPlusTrainer(config, delay=0)
values = trainer.train(10000)
```

**Key improvements:**
- **RM+ truncation**: R(a) = max(R(a) + Δr, 0) — regrets never go negative
- **Weighted averaging**: Later strategies get more weight
- **Alternating updates**: Update one player per iteration
- **Convergence**: O(1/T)

### NormalHedge

Parameter-free algorithm using half-normal potential.

```python
from normal_hedge import NormalHedgeTrainer

trainer = NormalHedgeTrainer(config)
values = trainer.train(10000)
```

**Key features:**
- **Potential function**: φ(x,c) = exp(max(x,0)² / 2c)
- **Automatic scale**: c chosen so average potential = e
- **Exponential weighting**: w(a) = (R⁺/c) × exp(R⁺²/2c)

### NormalHedge+ (Novel)

Our hybrid combining NormalHedge with RM+ truncation.

```python
from normal_hedge_plus import NormalHedgePlusTrainer

trainer = NormalHedgePlusTrainer(config)
values = trainer.train(10000)
```

**Motivation**: Combine the best of both worlds—exponential weighting for sharp strategy updates, RM+ truncation for faster recovery.

## 📈 Experimental Results

### Error from Nash Equilibrium

| Configuration | Iters | CFR | CFR+ | NormalHedge | NormalHedge+ |
|---------------|-------|-----|------|-------------|--------------|
| Standard (1,1) | 10K | 0.0050 | **0.0003** | 0.0388 | 0.0615 |
| Standard (1,1) | 100K | 0.0185 | 0.0122 | **0.0112** | 0.0123 |
| Large Bet (1,2) | 10K | 0.0525 | 0.1266 | 0.0446 | **0.0247** |
| Scaled (2,2) | 100K | 0.0710 | 0.0292 | **0.0108** | 0.0444 |

### Key Findings

1. **CFR+ excels at low iterations** — 94% error reduction over CFR at 10K iterations
2. **NormalHedge wins asymptotically** — Best accuracy at 100K iterations
3. **Pure strategies converge fast** — All algorithms quickly learn "always fold Jack facing bet"
4. **Mixed strategies are harder** — Jack bluffing (Nash: 1/3) shows persistent errors

### Strategy Convergence

| Info Set | Action | Nash | CFR | CFR+ | NH | NH+ |
|----------|--------|------|-----|------|-----|-----|
| J | BET | 0.333 | **0.283** | 0.226 | 0.146 | 0.225 |
| Q | CHECK | 1.000 | **1.000** | 0.993 | **1.000** | 0.991 |
| K | BET | 1.000 | **0.854** | 0.699 | 0.444 | 0.672 |
| Jb | FOLD | 1.000 | **1.000** | **1.000** | **1.000** | **1.000** |
| Kb | CALL | 1.000 | **1.000** | **1.000** | **1.000** | **1.000** |

## 🎮 Interactive Play

Play against a trained AI:

```bash
python interactive_play.py
```

## 📄 Academic Report

A comprehensive NeurIPS-format report is included:

```bash
# Compile the LaTeX report
pdflatex finalreport.tex
```

The report includes:
- Detailed algorithm descriptions with pseudocode
- Theoretical background on regret minimization
- Comprehensive experimental results
- Strategy convergence analysis
- Discussion and future work

## 🔧 Configuration Options

### Game Configuration

```python
from kuhn_poker import GameConfig

# Standard game
config = GameConfig(ante=1, bet_size=1)

# Large bet
config = GameConfig(ante=1, bet_size=2)

# Large ante
config = GameConfig(ante=2, bet_size=1)

# Scaled up
config = GameConfig(ante=2, bet_size=2)
```

### Training Configuration

```python
# CFR+ with delay parameter
trainer = CFRPlusTrainer(config, delay=100)

# More iterations for better convergence
values = trainer.train(100000)
```

## 📊 Generated Plots

The experiments generate several visualization files:

| File | Description |
|------|-------------|
| `exp_comprehensive_summary.png` | 6-panel summary of all experiments |
| `strategy_convergence_analysis.png` | Strategy convergence to Nash equilibrium |
| `exp_convergence_std_100k.png` | Convergence curves (standard config) |
| `exp_error_comparison.png` | Error comparison bar chart |
| `exp_timing_comparison.png` | Training time comparison |

## 📚 References

1. **Zinkevich et al. (2007)**: "Regret Minimization in Games with Incomplete Information" — CFR
2. **Tammelin (2014)**: "Solving Large Imperfect Information Games Using CFR+" — CFR+
3. **Chaudhuri, Freund, Hsu (2009)**: "A Parameter-free Hedging Algorithm" — NormalHedge
4. **Kuhn (1950)**: "A Simplified Two-Person Poker"
5. **Brown & Sandholm (2019)**: "Superhuman AI for Multiplayer Poker" — Pluribus

## 🔬 Future Work

- **Larger games**: Test on Texas Hold'em
- **Monte Carlo variants**: Implement MCCFR for scaling
- **Deep learning**: Combine with neural networks (Deep CFR)
- **Theoretical analysis**: Derive convergence bounds for NormalHedge+

## 📝 Citation

If you use this code in your research, please cite:

```bibtex
@misc{radwan2024regret,
  author = {Radwan, Yousef},
  title = {Regret Minimization Algorithms for Kuhn Poker},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/yradwan147/RegretMinimizationKuhnPoker}
}
```

## 📄 License

MIT License - Free to use and modify for research and education.

## 👤 Author

**Yousef Radwan**  
King Abdullah University of Science and Technology (KAUST)  
yousef.radwan@kaust.edu.sa
