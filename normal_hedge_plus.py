"""
NormalHedge+ Algorithm Implementation for Kuhn Poker
A modification of NormalHedge with Regret Matching+ (RM+) truncation.

Based on NormalHedge ("A Parameter-free Hedging Algorithm" by Chaudhuri, Freund, Hsu)
with the critical modification from RM+ (Brown & Sandholm): cumulative regrets are
truncated to never fall below zero.

Key features:
1. Uses half-normal potential: φ(x,c) = exp((max{x,0}²)/(2c))
2. Scale c_t found via line search: average potential equals e
3. **NEW**: Cumulative regrets use RM+ truncation: R'_{i,t} = max{R'_{i,t-1} + r_{i,t}, 0}
4. Parameter-free: no learning rate tuning needed

Expected improvement:
- Faster adaptation to changing loss sequences
- Better "forgetting" of past poor performance
- Similar order-of-magnitude speedup as CFR+ vs CFR
"""
import numpy as np
import math
from typing import Dict, List, Tuple
from kuhn_poker import GameState, GameConfig, Action, Card


class InformationSetNHPlus:
    """
    Information set for NormalHedge+ algorithm.
    Tracks cumulative regrets with RM+ truncation and computes NormalHedge weights.
    """
    def __init__(self, num_actions: int):
        self.num_actions = num_actions
        # CRITICAL CHANGE: regret_sum now uses RM+ truncation (always >= 0)
        self.regret_sum = np.zeros(num_actions)  # Truncated cumulative regret R'_{I,a}
        self.c_scale = 1.0  # NH scale parameter c_I
        self.strategy = np.ones(num_actions) / num_actions  # Current strategy
        self.strategy_sum = np.zeros(num_actions)  # For computing average strategy
    
    def normalhedge_weight(self, R_plus: np.ndarray, c: float) -> np.ndarray:
        """
        Compute unnormalized NormalHedge weights.
        
        Formula: w[a] = (R_plus[a]/c) * exp((R_plus[a]²)/(2c))
        
        Note: Since R_plus is guaranteed >= 0 in NormalHedge+, the [·]+ operator
        in the original formula is redundant.
        
        Args:
            R_plus: Array of nonnegative R'_{I,a} values (already truncated)
            c: Scale parameter
            
        Returns:
            Unnormalized weights for each action
        """
        weights = np.zeros(self.num_actions)
        for i in range(self.num_actions):
            if R_plus[i] > 0:
                # Compute (R/c) * exp(R²/(2c))
                exponent = (R_plus[i] * R_plus[i]) / (2.0 * c)
                # Numerical stability: clamp exponent to prevent overflow
                exponent = min(exponent, 700.0)  # exp(700) is near max float
                weights[i] = (R_plus[i] / c) * math.exp(exponent)
            else:
                weights[i] = 0.0
        return weights
    
    def solve_c_scale(self, R_plus: np.ndarray) -> float:
        """
        Find scale c > 0 such that average potential equals e.
        
        Constraint: (1/|A|) * sum_a exp((R_plus[a]²)/(2c)) = e
        
        Uses bisection search. The left-hand side is monotone decreasing in c.
        
        Args:
            R_plus: Array of nonnegative R'_{I,a} values (already truncated)
            
        Returns:
            Scale parameter c
        """
        # If all regrets are non-positive, return any positive c
        if np.max(R_plus) <= 0.0:
            return 1.0
        
        def avg_potential(c: float) -> float:
            """Compute average potential for given c."""
            total = 0.0
            for rp in R_plus:
                exponent = (rp * rp) / (2.0 * c)
                # Numerical stability: clamp exponent
                exponent = min(exponent, 700.0)
                total += math.exp(exponent)
            return total / len(R_plus)
        
        # Find brackets [c_lo, c_hi] such that avg_potential(c_lo) > e > avg_potential(c_hi)
        c_lo = 1e-12
        c_hi = 1.0
        
        # Expand c_hi until avg_potential(c_hi) < e
        max_iterations = 100
        for _ in range(max_iterations):
            if avg_potential(c_hi) <= math.e:
                break
            c_hi *= 2.0
            if c_hi > 1e12:
                c_hi = 1e12
                break
        
        # Bisection search
        for _ in range(60):
            c_mid = 0.5 * (c_lo + c_hi)
            val = avg_potential(c_mid)
            
            if abs(val - math.e) < 1e-10:  # Converged
                return c_mid
            
            if val > math.e:
                # Need larger c to reduce potential
                c_lo = c_mid
            else:
                # Need smaller c to increase potential
                c_hi = c_mid
        
        return 0.5 * (c_lo + c_hi)
    
    def get_strategy(self) -> np.ndarray:
        """
        Get current strategy using NormalHedge weights.
        
        Formula:
        σ_I(a) ∝ (R'_{I,a}/c) * exp((R'_{I,a})²/(2c))
        
        Note: In NormalHedge+, R'_{I,a} is already >= 0, so no need for [·]+ operator.
        
        Returns:
            Current behavioral strategy (probability distribution)
        """
        # In NormalHedge+, regret_sum is already truncated (always >= 0)
        # So we don't need the max operation
        R_plus = self.regret_sum
        
        # Solve for scale parameter c
        self.c_scale = self.solve_c_scale(R_plus)
        
        # Compute NormalHedge weights
        weights = self.normalhedge_weight(R_plus, self.c_scale)
        
        # Normalize to get probability distribution
        weight_sum = np.sum(weights)
        if weight_sum > 0:
            self.strategy = weights / weight_sum
        else:
            # All regrets non-positive: use uniform distribution
            self.strategy = np.ones(self.num_actions) / self.num_actions
        
        return self.strategy
    
    def add_regret(self, action_idx: int, regret: float):
        """
        Add regret for a specific action with RM+ truncation.
        
        CRITICAL CHANGE: Implements RM+ truncation structure:
        R'_{I,a} = max{R'_{I,a} + regret, 0}
        
        This ensures cumulative regret never falls below zero, allowing actions
        to "forget" periods of poor performance and adapt faster when they
        start performing well again.
        
        Args:
            action_idx: Index of the action
            regret: Instantaneous regret to add
        """
        # RM+ truncation: cumulative regret never goes below zero
        self.regret_sum[action_idx] = max(self.regret_sum[action_idx] + regret, 0.0)
    
    def update_strategy_sum(self, reach_prob: float):
        """
        Update cumulative strategy (weighted by reach probability).
        
        Used for computing average strategy over all iterations.
        
        Args:
            reach_prob: Current player's reach probability to this infoset
        """
        self.strategy_sum += reach_prob * self.strategy
    
    def get_average_strategy(self) -> np.ndarray:
        """
        Get the average strategy across all iterations.
        
        Returns:
            Average behavioral strategy
        """
        normalizing_sum = np.sum(self.strategy_sum)
        if normalizing_sum > 0:
            return self.strategy_sum / normalizing_sum
        else:
            return np.ones(self.num_actions) / self.num_actions


class NormalHedgePlusTrainer:
    """
    NormalHedge+ trainer for Kuhn Poker.
    
    Implements parameter-free online learning via NormalHedge algorithm with
    Regret Matching+ (RM+) truncation for cumulative regrets.
    
    Key differences from vanilla NormalHedge:
    - Uses RM+ truncation: R'_{i,t} = max{R'_{i,t-1} + r_{i,t}, 0}
    - Expected to converge faster by "forgetting" past poor performance
    - Similar improvement as CFR+ over CFR (order of magnitude speedup)
    
    Key differences from CFR+:
    - Uses NormalHedge weighting instead of regret-matching proportional weights
    - No parameters to tune (scale c_t computed automatically)
    - Still maintains the RM+ truncation structure
    """
    def __init__(self, config: GameConfig):
        """
        Initialize NormalHedge+ trainer.
        
        Args:
            config: Game configuration
        """
        self.config = config
        self.info_sets: Dict[str, InformationSetNHPlus] = {}
        self.iteration = 0
    
    def get_info_set(self, key: str, num_actions: int) -> InformationSetNHPlus:
        """Get or create an information set."""
        if key not in self.info_sets:
            self.info_sets[key] = InformationSetNHPlus(num_actions)
        return self.info_sets[key]
    
    def train(self, num_iterations: int) -> List[float]:
        """
        Train the NormalHedge+ algorithm for a number of iterations.
        
        Args:
            num_iterations: Number of training iterations
            
        Returns:
            List of expected game values per iteration (for player 0)
        """
        expected_values = []
        
        for i in range(num_iterations):
            self.iteration = i
            
            # Deal random cards
            deck = self.config.get_deck()
            cards = [deck[0], deck[1]]
            
            # Create initial game state
            initial_state = GameState(self.config, cards)
            
            # Run NormalHedge+ for both players
            value = self.normalhedge_plus_cfr(initial_state, reach_prob_0=1.0, reach_prob_1=1.0)
            expected_values.append(value)
            
            if (i + 1) % 1000 == 0:
                print(f"Iteration {i + 1}/{num_iterations} - Expected value: {value:.6f}")
        
        return expected_values
    
    def normalhedge_plus_cfr(self, state: GameState, reach_prob_0: float, reach_prob_1: float) -> float:
        """
        Recursive NormalHedge+-CFR algorithm.
        
        Similar to vanilla CFR but uses NormalHedge+ for strategy computation
        (NormalHedge weights with RM+ truncated cumulative regrets).
        
        Args:
            state: Current game state
            reach_prob_0: Probability that player 0's strategy reaches this state
            reach_prob_1: Probability that player 1's strategy reaches this state
            
        Returns:
            Expected utility for player 0
        """
        # Terminal state - return payoff
        if state.is_terminal():
            return state.get_payoff(player=0)
        
        player = state.get_current_player()
        info_set_key = state.get_info_set(player)
        legal_actions = state.get_legal_actions()
        num_actions = len(legal_actions)
        
        # Get or create information set
        info_set = self.get_info_set(info_set_key, num_actions)
        strategy = info_set.get_strategy()
        
        # Reach probability for the opponent
        opponent_reach_prob = reach_prob_1 if player == 0 else reach_prob_0
        
        # Calculate counterfactual action values
        action_utilities = np.zeros(num_actions)
        for i, action in enumerate(legal_actions):
            next_state = state.apply_action(action)
            
            if player == 0:
                action_utilities[i] = self.normalhedge_plus_cfr(
                    next_state,
                    reach_prob_0 * strategy[i],
                    reach_prob_1
                )
            else:
                # For player 1, negate the utility (since cfr returns player 0's utility)
                action_utilities[i] = -self.normalhedge_plus_cfr(
                    next_state,
                    reach_prob_0,
                    reach_prob_1 * strategy[i]
                )
        
        # Expected utility for this information set
        expected_utility = np.sum(strategy * action_utilities)
        
        # Update regrets using counterfactual regret with RM+ truncation
        # r_{I,a} = v_I(a) - v_I(σ_I) (utility space)
        # For NormalHedge+, we use the regret identity directly.
        # The loss conversion ℓ_{I,a} = (1 - r_{I,a})/2 preserves action ordering,
        # so we can work directly with regrets (only the relative ordering matters for NH).
        for i in range(num_actions):
            regret = action_utilities[i] - expected_utility
            # add_regret now applies RM+ truncation internally
            info_set.add_regret(i, opponent_reach_prob * regret)
        
        # Update strategy sum (for computing average strategy)
        current_reach_prob = reach_prob_0 if player == 0 else reach_prob_1
        info_set.update_strategy_sum(current_reach_prob)
        
        return expected_utility if player == 0 else -expected_utility
    
    def get_strategy_profile(self) -> Dict[str, Dict[str, float]]:
        """
        Get the average strategy for all information sets in a readable format.
        
        Returns:
            Dictionary mapping infoset keys to action probability dictionaries
        """
        profile = {}
        
        for info_set_key, info_set in self.info_sets.items():
            avg_strategy = info_set.get_average_strategy()
            
            # Determine possible actions based on history
            history = info_set_key[1:]  # Remove card character
            
            if len(history) == 0:
                action_names = ["CHECK", "BET"]
            elif history == "c":
                action_names = ["CHECK", "BET"]
            elif history == "b":
                action_names = ["FOLD", "CALL"]
            elif history == "cb":
                action_names = ["FOLD", "CALL"]
            else:
                action_names = [f"Action{i}" for i in range(len(avg_strategy))]
            
            profile[info_set_key] = {
                action_names[i]: float(avg_strategy[i])
                for i in range(len(avg_strategy))
            }
        
        return profile

