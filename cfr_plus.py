"""
CFR+ (Counterfactual Regret Minimization Plus) Implementation
State-of-the-art variant of CFR with improved convergence rate.

Key differences from vanilla CFR:
1. Regret clipping: max{regret, 0} - regrets never go negative
2. Weighted averaging with delay parameter
3. Alternating player updates per iteration
4. Vector-form representation
"""
import numpy as np
from typing import Dict, List, Tuple
from kuhn_poker import GameState, GameConfig, Action, Card
import random


class InformationSetPlus:
    """
    Information set for CFR+ algorithm.
    Tracks regrets and strategies with CFR+ specific updates.
    """
    def __init__(self, num_actions: int):
        self.num_actions = num_actions
        self.regret_sum = np.zeros(num_actions)  # Cumulative regret+ (always >= 0)
        self.strategy_sum = np.zeros(num_actions)  # Weighted cumulative strategy
        self.strategy = np.ones(num_actions) / num_actions  # Current strategy
    
    def get_strategy(self) -> np.ndarray:
        """
        Get current strategy using Regret-Matching+.
        
        CFR+ formula:
        - If sum of positive regrets > 0: normalize by positive regrets
        - Otherwise: uniform strategy
        """
        # Sum of positive regrets (in CFR+, all regrets are >= 0)
        normalizing_sum = np.sum(self.regret_sum)
        
        if normalizing_sum > 0:
            # Normalize by positive regrets
            self.strategy = self.regret_sum / normalizing_sum
        else:
            # Uniform strategy if no positive regrets
            self.strategy = np.ones(self.num_actions) / self.num_actions
        
        return self.strategy
    
    def add_regret(self, action_idx: int, regret: float):
        """
        Add regret for a specific action using CFR+ update rule.
        
        CFR+ formula: R^{+,T}(I,a) = max{R^{+,T-1}(I,a) + regret, 0}
        """
        # Update cumulative regret with clipping at 0
        self.regret_sum[action_idx] = max(self.regret_sum[action_idx] + regret, 0.0)
    
    def update_strategy_sum(self, reach_prob: float, weight: float):
        """
        Update cumulative strategy with weighting (for averaging).
        
        CFR+ formula: s_I[a] <- s_I[a] + π_{-i}[I] * σ[a][I] * w
        
        Args:
            reach_prob: Opponent's reach probability π_{-i}[I]
            weight: Weighting factor w = max{t - d, 0}
        """
        self.strategy_sum += reach_prob * self.strategy * weight
    
    def get_average_strategy(self) -> np.ndarray:
        """Get the average strategy across all iterations (weighted)."""
        normalizing_sum = np.sum(self.strategy_sum)
        if normalizing_sum > 0:
            return self.strategy_sum / normalizing_sum
        else:
            return np.ones(self.num_actions) / self.num_actions


class CFRPlusTrainer:
    """
    CFR+ trainer for Kuhn Poker.
    
    Implements the state-of-the-art CFR+ algorithm with:
    - Regret clipping (no negative regrets)
    - Weighted averaging with delay parameter
    - Alternating player updates
    """
    def __init__(self, config: GameConfig, delay: int = 0):
        """
        Initialize CFR+ trainer.
        
        Args:
            config: Game configuration
            delay: Averaging delay parameter (d). 
                   Weight w = max{t - d, 0} for iteration t.
                   Typical values: 0 (no delay), 100, 500
        """
        self.config = config
        self.delay = delay
        self.info_sets: Dict[str, InformationSetPlus] = {}
        self.iteration = 0
    
    def get_info_set(self, key: str, num_actions: int) -> InformationSetPlus:
        """Get or create an information set."""
        if key not in self.info_sets:
            self.info_sets[key] = InformationSetPlus(num_actions)
        return self.info_sets[key]
    
    def train(self, num_iterations: int) -> List[float]:
        """
        Train the CFR+ algorithm for a number of iterations.
        
        CFR+ uses alternating updates: each iteration updates one player.
        
        Returns:
            List of expected game values per iteration (for player 0)
        """
        expected_values = []
        
        for t in range(1, num_iterations + 1):
            self.iteration = t
            
            # Calculate weight for this iteration: w = max{t - d, 0}
            weight = max(t - self.delay, 0)
            
            # Deal random cards
            deck = self.config.get_deck()
            cards = [deck[0], deck[1]]
            initial_state = GameState(self.config, cards)
            
            # Alternating updates: update one player per iteration
            # Even iterations: update player 0, odd iterations: update player 1
            updating_player = (t - 1) % 2
            
            # Run CFR+ for the updating player
            value = self.cfr_plus(
                state=initial_state,
                updating_player=updating_player,
                reach_prob_0=1.0,
                reach_prob_1=1.0,
                weight=weight
            )
            
            # Store value from player 0's perspective
            if updating_player == 0:
                expected_values.append(value)
            else:
                expected_values.append(-value)  # Flip sign for player 1
            
            if t % 1000 == 0:
                print(f"Iteration {t}/{num_iterations} - Expected value: {value:.6f}")
        
        return expected_values
    
    def cfr_plus(
        self, 
        state: GameState, 
        updating_player: int,
        reach_prob_0: float, 
        reach_prob_1: float,
        weight: float
    ) -> float:
        """
        Recursive CFR+ algorithm (vector-form, alternating updates).
        
        Args:
            state: Current game state
            updating_player: Which player's regrets are being updated (0 or 1)
            reach_prob_0: Reach probability for player 0
            reach_prob_1: Reach probability for player 1
            weight: Weighting factor w = max{t - d, 0}
        
        Returns:
            Expected utility for the updating player
        """
        # Terminal state - return payoff
        if state.is_terminal():
            return state.get_payoff(player=updating_player)
        
        current_player = state.get_current_player()
        info_set_key = state.get_info_set(current_player)
        legal_actions = state.get_legal_actions()
        num_actions = len(legal_actions)
        
        # Get or create information set
        info_set = self.get_info_set(info_set_key, num_actions)
        strategy = info_set.get_strategy()
        
        # If current player is the updating player: regret update pass
        if current_player == updating_player:
            # Calculate utilities for each action
            action_utilities = np.zeros(num_actions)
            
            for i, action in enumerate(legal_actions):
                next_state = state.apply_action(action)
                
                if updating_player == 0:
                    action_utilities[i] = self.cfr_plus(
                        next_state,
                        updating_player,
                        reach_prob_0 * strategy[i],
                        reach_prob_1,
                        weight
                    )
                else:
                    action_utilities[i] = self.cfr_plus(
                        next_state,
                        updating_player,
                        reach_prob_0,
                        reach_prob_1 * strategy[i],
                        weight
                    )
            
            # Expected utility for this information set
            expected_utility = np.sum(strategy * action_utilities)
            
            # Get opponent's reach probability for regret weighting
            opponent_reach_prob = reach_prob_1 if updating_player == 0 else reach_prob_0
            
            # Update regrets using CFR+ formula: max{R + regret, 0}
            for i in range(num_actions):
                regret = action_utilities[i] - expected_utility
                info_set.add_regret(i, opponent_reach_prob * regret)
            
            return expected_utility
        
        # Else: opponent is acting - strategy accumulation pass
        else:
            # Calculate expected utility and accumulate strategy
            expected_utility = 0.0
            
            # Get current player's reach probability for strategy weighting
            current_reach_prob = reach_prob_0 if current_player == 0 else reach_prob_1
            
            # Update cumulative strategy (weighted)
            if weight > 0:  # Only accumulate if weight is positive
                info_set.update_strategy_sum(current_reach_prob, weight)
            
            # Traverse all actions
            for i, action in enumerate(legal_actions):
                next_state = state.apply_action(action)
                
                if current_player == 0:
                    action_utility = self.cfr_plus(
                        next_state,
                        updating_player,
                        reach_prob_0 * strategy[i],
                        reach_prob_1,
                        weight
                    )
                else:
                    action_utility = self.cfr_plus(
                        next_state,
                        updating_player,
                        reach_prob_0,
                        reach_prob_1 * strategy[i],
                        weight
                    )
                
                expected_utility += strategy[i] * action_utility
            
            return expected_utility
    
    def get_strategy_profile(self) -> Dict[str, Dict[str, float]]:
        """
        Get the average strategy for all information sets in a readable format.
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



