# Step-by-Step Kuhn Poker Example: 4 Algorithms Compared
## A Beginner-Friendly Walkthrough

This document walks through **two complete iterations** of Kuhn Poker using each of the four regret minimization algorithms. We'll explain every symbol, every calculation, and why we're doing each step.

---

## Table of Contents

1. [Part 1: Understanding the Basics](#part-1-understanding-the-basics)
2. [Part 2: Setting Up Our Example](#part-2-setting-up-our-example)
3. [Part 3: Algorithm 1 - CFR (Vanilla)](#part-3-algorithm-1---cfr-vanilla)
4. [Part 4: Algorithm 2 - CFR+](#part-4-algorithm-2---cfr)
5. [Part 5: Algorithm 3 - NormalHedge](#part-5-algorithm-3---normalhedge)
6. [Part 6: Algorithm 4 - NormalHedge+](#part-6-algorithm-4---normalhedge)
7. [Part 7: Summary and Comparison](#part-7-summary-and-comparison)

---

# Part 1: Understanding the Basics

Before we dive into the algorithms, let's make sure we understand **what we're trying to do** and **what all the symbols mean**.

## 1.1 What is Kuhn Poker?

Kuhn Poker is a tiny, simplified version of poker with just 3 cards:
- **Jack (J)** - the worst card
- **Queen (Q)** - the middle card  
- **King (K)** - the best card

### The Rules

1. Both players put **1 chip** into the pot (this is called the "ante")
2. Each player gets **one card** (dealt randomly)
3. **Player 0** acts first and can:
   - **CHECK** (pass, don't bet anything)
   - **BET** (put 1 more chip into the pot)
4. **Player 1** then responds:
   - If Player 0 checked: Player 1 can CHECK or BET
   - If Player 0 bet: Player 1 can FOLD (give up) or CALL (match the bet)
5. If Player 0 checked, Player 1 bet, then Player 0 gets one more choice: FOLD or CALL
6. **Showdown**: If nobody folded, the higher card wins!

### Example Game
```
Player 0 has: Jack
Player 1 has: Queen

Player 0 thinks: "I have a bad card, but maybe I can bluff!"
Player 0 chooses: BET (puts 1 chip in)

Player 1 thinks: "I have a Queen, that beats Jack. I'll call."
Player 1 chooses: CALL (puts 1 chip in)

Showdown: Queen > Jack
Result: Player 1 wins the pot (2 chips from ante + 2 chips from bets = 4 chips)
Player 0 loses 2 chips total (1 ante + 1 bet)
```

---

## 1.2 What is an "Information Set"?

An **information set** is everything a player knows at a decision point:
- What card they have
- What actions have happened so far
- (But NOT what card the opponent has!)

We write information sets as a string like `"Jcb"`:
- `J` = Player has a Jack
- `c` = Someone checked
- `b` = Someone bet

### Player 0's Information Sets

| Code | Meaning | What Can Player 0 Do? |
|------|---------|----------------------|
| `J` | I have Jack, it's my first turn | CHECK or BET |
| `Q` | I have Queen, it's my first turn | CHECK or BET |
| `K` | I have King, it's my first turn | CHECK or BET |
| `Jcb` | I have Jack, I checked, opponent bet | FOLD or CALL |
| `Qcb` | I have Queen, I checked, opponent bet | FOLD or CALL |
| `Kcb` | I have King, I checked, opponent bet | FOLD or CALL |

### Player 1's Information Sets

| Code | Meaning | What Can Player 1 Do? |
|------|---------|----------------------|
| `Jc` | I have Jack, opponent checked | CHECK or BET |
| `Qc` | I have Queen, opponent checked | CHECK or BET |
| `Kc` | I have King, opponent checked | CHECK or BET |
| `Jb` | I have Jack, opponent bet | FOLD or CALL |
| `Qb` | I have Queen, opponent bet | FOLD or CALL |
| `Kb` | I have King, opponent bet | FOLD or CALL |

---

## 1.3 What is "Regret"?

**Regret** is the feeling of "I wish I had done something different."

In math terms: **How much better would I have done if I had always chosen a different action?**

### Simple Example

Imagine you're at info set "J" (you have Jack, first turn) and you chose CHECK.
- CHECK gave you: -1 chip (you lost)
- If you had chosen BET, you would have gotten: +1 chip (opponent folded)

Your **regret for BET** = (what BET would have given) - (what you actually got)
= (+1) - (-1) = **+2**

This means: "I really wish I had bet! I missed out on 2 chips."

### Key Insight

**Positive regret** = "I wish I had played this action more"
**Negative regret** = "I'm glad I didn't play this action more"

---

## 1.4 What is a "Strategy"?

A **strategy** tells us the probability of choosing each action.

We write it as: `σ = [0.3, 0.7]`

This means:
- 30% chance of choosing the first action (e.g., CHECK)
- 70% chance of choosing the second action (e.g., BET)

**Uniform strategy**: `σ = [0.5, 0.5]` means 50-50, equally likely to choose either.

---

## 1.5 Key Symbols We'll Use

| Symbol | Name | What It Means |
|--------|------|---------------|
| `σ` (sigma) | Strategy | Probability of each action, like [0.5, 0.5] |
| `R` | Cumulative Regret | Total regret accumulated over all iterations |
| `R⁺` | Positive Regret | max(R, 0) - we only care about positive regret |
| `r` | Instantaneous Regret | Regret from just this one iteration |
| `v` | Value/Utility | How many chips we win (positive) or lose (negative) |
| `π₀` (pi-zero) | Player 0's Reach | Probability that Player 0's strategy leads here |
| `π₁` (pi-one) | Player 1's Reach | Probability that Player 1's strategy leads here |

---

# Part 2: Setting Up Our Example

## 2.1 Initial State

Before we start any iterations, we set everything to zero:

```
For every information set (like "J", "Qc", "Kb", etc.):
    regret_sum = [0, 0]      ← No regrets yet (we haven't played!)
    strategy_sum = [0, 0]    ← No strategies accumulated yet
    strategy = [0.5, 0.5]    ← Start with 50-50 for each action
```

## 2.2 Our Two Iterations

We'll trace through two hands:
- **Iteration 1**: Player 0 gets **Jack**, Player 1 gets **Queen**
- **Iteration 2**: Player 0 gets **Queen**, Player 1 gets **King**

Let's see how each algorithm handles these!

---

# Part 3: Algorithm 1 - CFR (Vanilla)

CFR stands for **C**ounter**f**actual **R**egret Minimization. It's the original, foundational algorithm.

## 3.1 The Key Idea

1. Start with a 50-50 strategy
2. Play out the game and see what happens
3. Calculate regret: "How much better would other actions have been?"
4. Adjust strategy: Put more weight on actions with high positive regret
5. Repeat thousands of times → Strategy converges to optimal!

## 3.2 The Main Equations

### Equation 1: How to Convert Regret into a Strategy

```
Step 1: Take only positive regrets
        R⁺[action] = max(R[action], 0)
        
        Example: If R = [-2, 5], then R⁺ = [0, 5]
        (We ignore the -2 because we can't have negative probability!)

Step 2: Normalize to get probabilities
        σ[action] = R⁺[action] / (sum of all R⁺)
        
        Example: R⁺ = [0, 5]
        Sum = 0 + 5 = 5
        σ = [0/5, 5/5] = [0, 1]
        (This means: always choose action 2!)

Step 3: If all regrets are zero or negative, use uniform
        σ = [0.5, 0.5]
```

### Equation 2: How to Update Regret

```
For each action a:
    r[a] = opponent_reach × (value of action a - expected value)
    R[a] = R[a] + r[a]
```

Let's see what each part means:
- **value of action a**: What we'd get if we always chose action a
- **expected value**: What we actually expect to get with our current strategy
- **opponent_reach**: How likely the OPPONENT's strategy led us here (not our own!)

---

## 3.3 Iteration 1: Jack vs Queen (CFR)

### The Deal
```
┌─────────────────────────────────────────────┐
│  ITERATION 1                                │
│  Player 0 gets: Jack (the worst card)       │
│  Player 1 gets: Queen (the middle card)     │
│  Starting pot: 2 chips (1 ante from each)   │
└─────────────────────────────────────────────┘
```

### Step 1: Player 0's Turn (Info Set "J")

Player 0 has Jack and must choose: CHECK or BET?

**What's our current strategy?**
```
All regrets are 0 (we just started!)
regret_sum["J"] = [0, 0]

Apply Equation 1:
  R⁺ = [max(0,0), max(0,0)] = [0, 0]
  Sum of R⁺ = 0
  
  Sum is zero, so use uniform strategy:
  σ["J"] = [0.5, 0.5]
  
  This means: 50% CHECK, 50% BET
```

**Reach probabilities:**
```
π₀ = 1.0  (Player 0 can always reach this point - it's their first decision)
π₁ = 1.0  (Player 1 hasn't made any choices yet)
```

Now we need to figure out the **value** of each action. To do this, we explore both branches of the game tree.

---

### Step 2: Explore the CHECK Branch

Player 0 chooses CHECK. Now it's Player 1's turn.

```
Game state: Player 0 checked
History: "c"
Now at: Player 1's info set "Qc" (Queen, opponent checked)
```

**Player 1's strategy at "Qc":**
```
regret_sum["Qc"] = [0, 0] (first time here)
σ["Qc"] = [0.5, 0.5]  (50% CHECK, 50% BET)
```

**Update reach probabilities:**
```
When Player 0 chose CHECK with probability 0.5:
  π₀ = 1.0 × 0.5 = 0.5   (Player 0's choices led here with prob 0.5)
  π₁ = 1.0               (Player 1 still hasn't acted)
```

Now explore Player 1's options:

#### Branch 2a: Player 1 also CHECKS
```
Game ends! Both checked → Showdown
History: "cc"
Compare cards: Jack vs Queen
Queen wins! (Queen > Jack)

Player 0's payoff = -1 chip (loses the ante)
```

#### Branch 2b: Player 1 BETS
```
History: "cb"
Now Player 0 must respond at info set "Jcb"
(Jack, after check-bet sequence)
```

---

### Step 3: Player 0's Response at "Jcb"

Player 0 has Jack, checked earlier, and now Player 1 bet. Should we FOLD or CALL?

**Current strategy at "Jcb":**
```
regret_sum["Jcb"] = [0, 0]
σ["Jcb"] = [0.5, 0.5]  (50% FOLD, 50% CALL)
```

**Explore both options:**

#### If Player 0 FOLDS:
```
History: "cbf" (check, bet, fold)
Game ends! Player 0 gives up.
Player 0's payoff = -1 chip (loses just the ante)
```

#### If Player 0 CALLS:
```
History: "cbc" (check, bet, call)
Showdown: Jack vs Queen
Queen wins!
Player 0's payoff = -2 chips (loses ante + the bet they called)
```

---

### Step 4: Calculate Values at "Jcb"

Now we have the payoffs. Let's work backwards to calculate regrets.

**Values for each action at "Jcb":**
```
v[FOLD] = -1  (lose 1 chip)
v[CALL] = -2  (lose 2 chips)
```

**Expected value with our current strategy:**
```
v_expected = σ[FOLD] × v[FOLD] + σ[CALL] × v[CALL]
           = 0.5 × (-1) + 0.5 × (-2)
           = -0.5 + -1.0
           = -1.5 chips

This means: With our 50-50 strategy, we expect to lose 1.5 chips on average.
```

**Instantaneous regret for each action:**
```
What's the opponent's reach probability here?
  π₁ = 1.0 × 0.5 = 0.5  (Player 1 chose BET with probability 0.5)

r[FOLD] = π₁ × (v[FOLD] - v_expected)
        = 0.5 × ((-1) - (-1.5))
        = 0.5 × (0.5)
        = 0.25

        Meaning: "FOLD is 0.5 better than average, weighted by how often we get here"

r[CALL] = π₁ × (v[CALL] - v_expected)
        = 0.5 × ((-2) - (-1.5))
        = 0.5 × (-0.5)
        = -0.25

        Meaning: "CALL is 0.5 worse than average"
```

**Update cumulative regret (CFR rule):**
```
regret_sum["Jcb"] = [0, 0] + [0.25, -0.25] = [0.25, -0.25]

Interpretation:
  - FOLD has positive regret (+0.25): "I wish I'd folded more!"
  - CALL has negative regret (-0.25): "I'm glad I didn't call more."
```

The value we return from "Jcb" is the expected value: **-1.5**

---

### Step 5: Calculate Values at "Qc" (Player 1's node)

We're back at Player 1's decision with Queen.

**Values from Player 1's perspective:**
```
v[CHECK] = +1  (Player 1 wins! They get the 1 chip ante from P0)
v[BET] = +1.5  (Expected: sometimes P0 folds giving +1, sometimes calls giving +2)

Wait, let's be careful about perspective here!

When P1 bets:
  - If P0 folds: P1 wins the ante = +1 for P1
  - If P0 calls: P1 wins ante + bet = +2 for P1
  
With P0's 50-50 strategy at "Jcb":
  v[BET] for P1 = 0.5 × (+1) + 0.5 × (+2) = +1.5
```

**Expected value for Player 1:**
```
v_expected = 0.5 × (+1) + 0.5 × (+1.5) = +1.25
```

**Regrets for Player 1 at "Qc":**
```
π₀ at this node = 0.5 (P0 chose CHECK with prob 0.5)

r[CHECK] = 0.5 × ((+1) - (+1.25)) = 0.5 × (-0.25) = -0.125
r[BET] = 0.5 × ((+1.5) - (+1.25)) = 0.5 × (+0.25) = +0.125

regret_sum["Qc"] = [-0.125, +0.125]
```

**Value returned to Player 0** (flip the sign since it's zero-sum):
```
Value of CHECK branch for P0 = -1.25
(P1 expects +1.25, so P0 expects -1.25)
```

---

### Step 6: Explore the BET Branch

Back at the very beginning, let's see what happens if Player 0 BETs instead.

```
Player 0 chooses BET
History: "b"
Now at: Player 1's info set "Qb" (Queen, opponent bet)
```

**Player 1's strategy at "Qb":**
```
regret_sum["Qb"] = [0, 0]
σ["Qb"] = [0.5, 0.5]  (50% FOLD, 50% CALL)
```

#### If Player 1 FOLDS:
```
History: "bf"
Player 0 wins the pot!
Player 0's payoff = +1 chip (wins the ante P1 put in)
```

#### If Player 1 CALLS:
```
History: "bc"
Showdown: Jack vs Queen
Queen wins!
Player 0's payoff = -2 chips (loses ante + bet)
```

**Values for P0 when they bet:**
```
v[P1 FOLDS] = +1  (P0 wins)
v[P1 CALLS] = -2  (P0 loses with Jack)

With P1's 50-50 strategy:
v[BET branch] = 0.5 × (+1) + 0.5 × (-2) = -0.5
```

---

### Step 7: Calculate Values at "J" (The Root)

Now we know both branches:
```
v[CHECK] = -1.25  (expected loss from the CHECK branch)
v[BET] = -0.5     (expected loss from the BET branch)
```

**Wait, both are losses?** Yes! Player 0 has the Jack (worst card), so they expect to lose on average. But BET loses less than CHECK because sometimes the bluff works!

**Expected value with 50-50 strategy:**
```
v_expected = 0.5 × (-1.25) + 0.5 × (-0.5)
           = -0.625 + -0.25
           = -0.875
```

**Instantaneous regrets:**
```
Opponent reach π₁ = 1.0 (P1 hasn't acted yet at the root)

r[CHECK] = 1.0 × ((-1.25) - (-0.875))
         = 1.0 × (-0.375)
         = -0.375

         "CHECK is worse than average by 0.375"

r[BET] = 1.0 × ((-0.5) - (-0.875))
       = 1.0 × (0.375)
       = 0.375

       "BET is better than average by 0.375"
```

**Update cumulative regret:**
```
regret_sum["J"] = [0, 0] + [-0.375, 0.375] = [-0.375, 0.375]

Interpretation:
  - CHECK has negative regret: "Checking is bad with Jack"
  - BET has positive regret: "I should bet (bluff) more with Jack!"
```

---

### Step 8: Iteration 1 Complete! Summary for CFR

After one iteration (Jack vs Queen), here are our cumulative regrets:

| Info Set | Action 0 | Action 1 | Meaning |
|----------|----------|----------|---------|
| J | -0.375 (CHECK) | +0.375 (BET) | Should bluff more with Jack! |
| Jcb | +0.25 (FOLD) | -0.25 (CALL) | Should fold more with Jack facing bet |
| Qc | -0.125 (CHECK) | +0.125 (BET) | With Queen, betting is slightly better |
| Qb | -0.75 (FOLD) | +0.75 (CALL) | With Queen facing bet, should call! |

---

### Step 9: How Strategy Changes for Iteration 2

Now let's see how the regrets affect our next strategy!

**At info set "J" (Jack, first turn):**
```
regret_sum["J"] = [-0.375, 0.375]

Step 1: Take positive parts only
  R⁺ = [max(-0.375, 0), max(0.375, 0)] = [0, 0.375]

Step 2: Normalize
  Sum = 0 + 0.375 = 0.375
  σ["J"] = [0/0.375, 0.375/0.375] = [0, 1]

NEW STRATEGY: Always BET with Jack!
```

The algorithm learned: **With Jack, you should bluff (bet) because folding is even worse!**

**At info set "Jcb" (Jack, after check-bet):**
```
regret_sum["Jcb"] = [0.25, -0.25]
R⁺ = [0.25, 0]
Sum = 0.25
σ["Jcb"] = [1, 0]

NEW STRATEGY: Always FOLD with Jack when facing a bet!
```

This makes sense! If you have Jack and opponent bets, they probably have a better card. Fold!

---

# Part 4: Algorithm 2 - CFR+

CFR+ is an improved version of CFR that converges faster. The main difference is **one simple change** to how we update regrets.

## 4.1 The Key Difference

| CFR (Vanilla) | CFR+ |
|---------------|------|
| `R = R + r` | `R = max(R + r, 0)` |
| Regret can go very negative | Regret is **never allowed to go below zero** |

That's it! Just add a `max(..., 0)` to the regret update.

### Why Does This Help?

Imagine an action that was terrible for 100 iterations and accumulated regret of -1000.

**CFR**: The action must earn +1000 regret before it gets any weight again. This takes a long time!

**CFR+**: The negative regret is immediately "forgiven." As soon as the action starts being good, it gets weight right away.

```
Example:
  Iteration 100: R = -1000
  Iteration 101: r = +50 (action is good this time!)
  
  CFR:  R = -1000 + 50 = -950 (still negative, still no weight)
  CFR+: R = max(-1000 + 50, 0) = max(-950, 0) = 0 (reset! ready to gain weight)
  
  Iteration 102: r = +50 again
  CFR:  R = -950 + 50 = -900 (still no weight...)
  CFR+: R = max(0 + 50, 0) = 50 (has positive weight now!)
```

## 4.2 Iteration 1: Jack vs Queen (CFR+)

Everything is the same as CFR **until we update regrets**. Let's see the difference:

### At Info Set "Jcb"
```
Instantaneous regrets (same as CFR):
  r[FOLD] = +0.25
  r[CALL] = -0.25

CFR update:
  regret_sum["Jcb"] = [0 + 0.25, 0 + (-0.25)] = [0.25, -0.25]

CFR+ update:
  regret_sum["Jcb"][FOLD] = max(0 + 0.25, 0) = max(0.25, 0) = 0.25  ✓ same
  regret_sum["Jcb"][CALL] = max(0 + (-0.25), 0) = max(-0.25, 0) = 0  ← DIFFERENT!

CFR+ result: regret_sum["Jcb"] = [0.25, 0]
```

The negative regret for CALL got **truncated to zero**!

### At Info Set "J"
```
Instantaneous regrets (same as CFR):
  r[CHECK] = -0.375
  r[BET] = +0.375

CFR update:
  regret_sum["J"] = [-0.375, 0.375]

CFR+ update:
  regret_sum["J"][CHECK] = max(0 + (-0.375), 0) = 0  ← TRUNCATED!
  regret_sum["J"][BET] = max(0 + 0.375, 0) = 0.375

CFR+ result: regret_sum["J"] = [0, 0.375]
```

### Comparison After Iteration 1

| Info Set | CFR Regrets | CFR+ Regrets |
|----------|-------------|--------------|
| J | [-0.375, 0.375] | [0, 0.375] |
| Jcb | [0.25, -0.25] | [0.25, 0] |
| Qc | [-0.125, 0.125] | [0, 0.125] |
| Qb | [-0.75, 0.75] | [0, 0.75] |

**Notice**: All negative values in CFR become **zero** in CFR+.

### Visual Comparison
```
           CFR Regrets              CFR+ Regrets
           ─────────────            ─────────────
    J:     [-0.375, 0.375]          [0, 0.375]
              ↑                         ↑
           negative               truncated to 0!
           
   Jcb:    [0.25, -0.25]           [0.25, 0]
                   ↑                       ↑
                negative             truncated!
```

## 4.3 Why CFR+ is Faster

In iteration 2, both algorithms produce the same strategy at "J":
- σ["J"] = [0, 1] (always BET)

But if later iterations cause CHECK to become better, CFR+ will adapt faster because it doesn't have to "pay off" the negative regret debt.

---

# Part 5: Algorithm 3 - NormalHedge

NormalHedge is a completely different approach. Instead of simple proportional regret matching, it uses an **exponential weighting scheme**.

## 5.1 The Key Idea

CFR says: "Weight actions proportionally to regret"
NormalHedge says: "Weight actions exponentially based on regret squared"

### The Weight Formula

For each action with positive regret R⁺:
```
         R⁺         (R⁺)²
weight = ── × exp( ───── )
         c          2c
```

Where:
- `R⁺` = positive regret (same as CFR)
- `c` = a "scale" parameter (calculated automatically)
- `exp()` = the exponential function (e^x)

### What is this `c` parameter?

We find `c` by solving this equation:
```
Average of all potentials = e (Euler's number ≈ 2.718)

         (R₁⁺)²           (R₂⁺)²
exp( ───── ) + exp( ───── ) + ...
         2c              2c
─────────────────────────────────── = e
         number of actions
```

This is solved numerically (the algorithm searches for the right value of c).

## 5.2 Iteration 1: Jack vs Queen (NormalHedge)

### Step 1: Initial Strategy

At the start, all regrets are 0:
```
regret_sum["J"] = [0, 0]
R⁺ = [0, 0]

When all R⁺ = 0:
  All weights are 0 (because R⁺/c = 0)
  Use uniform strategy: σ = [0.5, 0.5]
```

### Step 2: Tree Traversal

The game tree traversal is **exactly the same as CFR**! We get the same instantaneous regrets.

### Step 3: Regret Update

NormalHedge uses the **same regret update as CFR** (no truncation):
```
regret_sum["J"] = [0, 0] + [-0.375, 0.375] = [-0.375, 0.375]
```

So after iteration 1, NormalHedge has the same regrets as CFR.

---

## 5.3 Iteration 2: How NormalHedge Computes Strategy

Now we have non-zero regrets at "J". Let's see how NormalHedge converts them to a strategy.

```
regret_sum["J"] = [-0.375, 0.375]
```

### Step 1: Extract Positive Regrets
```
R⁺ = [max(-0.375, 0), max(0.375, 0)] = [0, 0.375]
```

### Step 2: Find the Scale Parameter c

We need to solve:
```
(1/2) × [exp(0²/(2c)) + exp(0.375²/(2c))] = e

(1/2) × [exp(0) + exp(0.1406/(2c))] = e

(1/2) × [1 + exp(0.0703/c)] = e
```

Let's solve for c:
```
1 + exp(0.0703/c) = 2e ≈ 5.436
exp(0.0703/c) = 4.436
0.0703/c = ln(4.436) ≈ 1.490
c = 0.0703 / 1.490 ≈ 0.0472
```

So **c ≈ 0.0472**

### Step 3: Compute Weights

**For CHECK (R⁺ = 0):**
```
         0           0²
weight = ──── × exp( ────── )
        0.0472      2×0.0472

       = 0 × exp(0)
       = 0 × 1
       = 0
```

**For BET (R⁺ = 0.375):**
```
         0.375          0.375²
weight = ────── × exp( ──────── )
         0.0472        2×0.0472

       = 7.94 × exp(0.1406/0.0944)
       = 7.94 × exp(1.49)
       = 7.94 × 4.44
       ≈ 35.25
```

### Step 4: Normalize to Strategy
```
total_weight = 0 + 35.25 = 35.25

σ[CHECK] = 0 / 35.25 = 0
σ[BET] = 35.25 / 35.25 = 1

Strategy: σ["J"] = [0, 1]  (Always BET)
```

**Same result as CFR!** But with different regrets, NormalHedge would behave differently.

---

## 5.4 How NormalHedge Differs from CFR

Let's see what happens with regrets [1.0, 2.0]:

**CFR Regret Matching:**
```
R⁺ = [1, 2]
Sum = 3
σ = [1/3, 2/3] = [0.33, 0.67]
```
The second action gets twice the weight.

**NormalHedge:** (assuming c ≈ 0.5 for this example)
```
weight[0] = (1/0.5) × exp(1/(2×0.5)) = 2 × e^1 ≈ 5.44
weight[1] = (2/0.5) × exp(4/(2×0.5)) = 4 × e^4 ≈ 218.4

Total = 223.8
σ = [5.44/223.8, 218.4/223.8] = [0.024, 0.976]
```
The second action gets **40 times** the weight!

### Key Insight

**CFR**: Linear relationship (2× regret → 2× weight)
**NormalHedge**: Exponential relationship (2× regret → MUCH more weight)

NormalHedge is more "aggressive" - it strongly favors high-regret actions.

---

# Part 6: Algorithm 4 - NormalHedge+

NormalHedge+ combines:
- **NormalHedge's exponential weighting** (the strategy computation)
- **CFR+'s regret truncation** (the regret update)

## 6.1 The Formula

### Strategy Computation (Same as NormalHedge)
```
         R⁺         (R⁺)²
weight = ── × exp( ───── )
         c          2c
```

### Regret Update (Same as CFR+)
```
R = max(R + r, 0)    ← Truncated at zero!
```

## 6.2 Iteration 1: Jack vs Queen (NormalHedge+)

### Regret Update (Like CFR+)
```
At info set "J":
  r = [-0.375, 0.375]
  
  NormalHedge update:
    regret_sum["J"] = [0 + (-0.375), 0 + 0.375] = [-0.375, 0.375]
  
  NormalHedge+ update:
    regret_sum["J"][0] = max(0 + (-0.375), 0) = 0  ← TRUNCATED!
    regret_sum["J"][1] = max(0 + 0.375, 0) = 0.375
    
  Result: regret_sum["J"] = [0, 0.375]
```

### Comparison After Iteration 1

| Info Set | CFR | CFR+ | NormalHedge | NormalHedge+ |
|----------|-----|------|-------------|--------------|
| J | [-0.375, 0.375] | [0, 0.375] | [-0.375, 0.375] | [0, 0.375] |
| Jcb | [0.25, -0.25] | [0.25, 0] | [0.25, -0.25] | [0.25, 0] |

**Pattern:**
- CFR and NormalHedge have the same regrets (both can go negative)
- CFR+ and NormalHedge+ have the same regrets (both truncate at zero)

The difference is in how they compute strategies:
- CFR/CFR+ use linear weighting
- NormalHedge/NormalHedge+ use exponential weighting

---

## 6.3 Why Combine Truncation with Exponential Weighting?

**The hypothesis**: 
- CFR+ is faster than CFR because of truncation
- Maybe NormalHedge+ is faster than NormalHedge for the same reason?

**In practice**: The results are mixed. Sometimes NormalHedge+ helps, sometimes it doesn't. This is still an area of research!

---

# Part 7: Summary and Comparison

## 7.1 The Four Algorithms at a Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HOW TO COMPUTE STRATEGY                      │
├─────────────────────────────────┬───────────────────────────────────┤
│      LINEAR WEIGHTING           │      EXPONENTIAL WEIGHTING        │
│  (simple, proportional)         │  (aggressive, squared regret)     │
│                                 │                                   │
│        R⁺[a]                    │     R⁺[a]        (R⁺[a])²         │
│  σ = ─────────                  │  w = ───── × exp(──────)          │
│      Σ R⁺[b]                    │       c           2c              │
│                                 │                                   │
│  CFR and CFR+ use this          │  NormalHedge and NH+ use this     │
└─────────────────────────────────┴───────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         HOW TO UPDATE REGRET                         │
├─────────────────────────────────┬───────────────────────────────────┤
│      NO TRUNCATION              │      WITH TRUNCATION              │
│  (regrets can go negative)      │  (regrets stay ≥ 0)               │
│                                 │                                   │
│    R = R + r                    │    R = max(R + r, 0)              │
│                                 │                                   │
│  CFR and NormalHedge use this   │  CFR+ and NormalHedge+ use this   │
└─────────────────────────────────┴───────────────────────────────────┘
```

## 7.2 The 2×2 Matrix of Algorithms

|  | Linear Weighting | Exponential Weighting |
|--|------------------|----------------------|
| **No Truncation** | CFR | NormalHedge |
| **With Truncation** | CFR+ | NormalHedge+ |

## 7.3 Worked Example Summary

After **Iteration 1** (Jack vs Queen):

| Info Set | CFR | CFR+ | NormalHedge | NormalHedge+ |
|----------|-----|------|-------------|--------------|
| J (CHECK,BET) | [-0.38, **0.38**] | [0, **0.38**] | [-0.38, **0.38**] | [0, **0.38**] |
| Jcb (FOLD,CALL) | [**0.25**, -0.25] | [**0.25**, 0] | [**0.25**, -0.25] | [**0.25**, 0] |

**Bold** = positive regret (will get weight in next strategy)

All algorithms learned the same lessons:
- **BET with Jack** (bluffing is better than just checking and losing)
- **FOLD with Jack facing a bet** (calling is too expensive with the worst card)

## 7.4 Key Takeaways for Beginners

1. **All four algorithms are trying to do the same thing**: Find the best poker strategy by learning from regret.

2. **The core loop is the same**:
   - Compute a strategy from regrets
   - Play out the game
   - Update regrets based on "what could have been better"
   - Repeat thousands of times

3. **CFR vs CFR+**: CFR+ truncates negative regrets to zero, helping actions recover faster.

4. **CFR vs NormalHedge**: NormalHedge weights actions exponentially, not linearly.

5. **The "+" algorithms** (CFR+, NormalHedge+) add truncation to speed up convergence.

---

## 7.5 Quick Reference Card

### CFR (Vanilla)
```python
# Strategy from regrets
R_plus = max(regret_sum, 0)      # Only positive regrets
strategy = R_plus / sum(R_plus)  # Normalize

# Update regrets
regret_sum = regret_sum + new_regret  # Can go negative!
```

### CFR+
```python
# Strategy (same as CFR)
R_plus = max(regret_sum, 0)
strategy = R_plus / sum(R_plus)

# Update regrets (TRUNCATED)
regret_sum = max(regret_sum + new_regret, 0)  # Never below zero!
```

### NormalHedge
```python
# Strategy (exponential)
R_plus = max(regret_sum, 0)
c = solve_for_c(R_plus)  # Find scale parameter
weights = (R_plus / c) * exp(R_plus**2 / (2*c))
strategy = weights / sum(weights)

# Update regrets
regret_sum = regret_sum + new_regret  # Can go negative!
```

### NormalHedge+
```python
# Strategy (exponential, same as NormalHedge)
R_plus = max(regret_sum, 0)
c = solve_for_c(R_plus)
weights = (R_plus / c) * exp(R_plus**2 / (2*c))
strategy = weights / sum(weights)

# Update regrets (TRUNCATED)
regret_sum = max(regret_sum + new_regret, 0)  # Never below zero!
```

---

*End of Beginner-Friendly Walkthrough*

## Glossary

| Term | Definition |
|------|------------|
| **Ante** | Money put in the pot before cards are dealt |
| **Bluff** | Betting with a bad hand hoping opponent folds |
| **Counterfactual** | "What would have happened if..." |
| **Expected Value** | Average outcome weighted by probabilities |
| **Fold** | Give up and lose what you've put in |
| **Information Set** | Everything a player knows at a decision point |
| **Nash Equilibrium** | Strategy where neither player can improve by changing |
| **Reach Probability** | Probability of getting to a game state |
| **Regret** | How much better a different action would have been |
| **Showdown** | Revealing cards to see who wins |
| **Strategy** | Probabilities of choosing each action |
| **Truncation** | Cutting off negative values at zero |
