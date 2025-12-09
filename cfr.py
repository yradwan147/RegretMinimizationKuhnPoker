"""
Counterfactual Regret Minimization (CFR) Implementation
for Kuhn Poker using game tree structure.
"""
import numpy as np
from typing import Dict, List, Tuple
from kuhn_poker import GameState, GameConfig, Action, Card
import random


class InformationSet:
    """
    Represents an information set in the game tree.
    Tracks regrets and strategies for each possible action.
    """
    def __init__(self, num_actions: int):
        self.num_actions = num_actions
        self.regret_sum = np.zeros(num_actions)
        self.strategy_sum = np.zeros(num_actions)
        self.strategy = np.ones(num_actions) / num_actions
    
    def get_strategy(self) -> np.ndarray:
        """Get current strategy using regret matching"""
        # Positive regrets only
        positive_regrets = np.maximum(self.regret_sum, 0)
        normalizing_sum = np.sum(positive_regrets)
        
        if normalizing_sum > 0:
            self.strategy = positive_regrets / normalizing_sum
        else:
            # Uniform strategy if no positive regrets
            self.strategy = np.ones(self.num_actions) / self.num_actions
        
        return self.strategy
    
    def add_regret(self, action_idx: int, regret: float):
        """Add regret for a specific action"""
        self.regret_sum[action_idx] += regret
    
    def update_strategy_sum(self, reach_prob: float):
        """Update cumulative strategy (weighted by reach probability)"""
        self.strategy_sum += reach_prob * self.strategy
    
    def get_average_strategy(self) -> np.ndarray:
        """Get the average strategy across all iterations"""
        normalizing_sum = np.sum(self.strategy_sum)
        if normalizing_sum > 0:
            return self.strategy_sum / normalizing_sum
        else:
            return np.ones(self.num_actions) / self.num_actions


class CFRTrainer:
    """
    Counterfactual Regret Minimization trainer for Kuhn Poker.
    Uses game tree structure to traverse all possible game states.
    """
    def __init__(self, config: GameConfig):
        self.config = config
        self.info_sets: Dict[str, InformationSet] = {}
        self.iteration = 0
    
    def get_info_set(self, key: str, num_actions: int) -> InformationSet:
        """Get or create an information set"""
        if key not in self.info_sets:
            self.info_sets[key] = InformationSet(num_actions)
        return self.info_sets[key]
    
    def train(self, num_iterations: int) -> List[float]:
        """
        Train the CFR algorithm for a number of iterations.
        Returns list of expected game values per iteration.
        """
        expected_values = []
        
        for i in range(num_iterations):
            self.iteration = i
            
            # Deal random cards
            deck = self.config.get_deck()
            cards = [deck[0], deck[1]]
            
            # Create initial game state
            initial_state = GameState(self.config, cards)
            
            # Run CFR for both players
            value = self.cfr(initial_state, reach_prob_0=1.0, reach_prob_1=1.0)
            expected_values.append(value)
            
            if (i + 1) % 1000 == 0:
                print(f"Iteration {i + 1}/{num_iterations} - Expected value: {value:.6f}")
        
        return expected_values
    
    def cfr(self, state: GameState, reach_prob_0: float, reach_prob_1: float) -> float:
        """
        Recursive CFR algorithm.
        Returns the expected utility for player 0.
        
        Args:
            state: Current game state
            reach_prob_0: Probability that player 0's strategy reaches this state
            reach_prob_1: Probability that player 1's strategy reaches this state
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
        
        # Calculate action utilities
        action_utilities = np.zeros(num_actions)
        for i, action in enumerate(legal_actions):
            next_state = state.apply_action(action)
            
            if player == 0:
                action_utilities[i] = self.cfr(
                    next_state,
                    reach_prob_0 * strategy[i],
                    reach_prob_1
                )
            else:
                # For player 1, negate the utility (since cfr returns player 0's utility)
                action_utilities[i] = -self.cfr(
                    next_state,
                    reach_prob_0,
                    reach_prob_1 * strategy[i]
                )
        
        # Expected utility for this information set
        expected_utility = np.sum(strategy * action_utilities)
        
        # Update regrets
        for i in range(num_actions):
            regret = action_utilities[i] - expected_utility
            info_set.add_regret(i, opponent_reach_prob * regret)
        
        # Update strategy sum (for computing average strategy)
        current_reach_prob = reach_prob_0 if player == 0 else reach_prob_1
        info_set.update_strategy_sum(current_reach_prob)
        
        return expected_utility if player == 0 else -expected_utility
    
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
    
    def get_exploitability(self) -> float:
        """
        Calculate exploitability of current average strategy.
        This is a simplified version for demonstration.
        """
        # In a full implementation, this would compute the best response
        # and measure how much better it does than Nash equilibrium value
        # For now, return a placeholder
        return 0.0

