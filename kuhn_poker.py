"""
Kuhn Poker Game Implementation
A simple 3-card poker variant for game theory analysis.
"""
import random
from typing import List, Dict, Tuple, Optional
from enum import Enum


class Action(Enum):
    """Possible actions in Kuhn Poker"""
    CHECK = 0
    BET = 1
    FOLD = 2
    CALL = 3


class Card(Enum):
    """Card values in Kuhn Poker"""
    JACK = 0
    QUEEN = 1
    KING = 2
    
    def __lt__(self, other):
        return self.value < other.value


class GameConfig:
    """Configuration for Kuhn Poker game rules"""
    def __init__(self, ante: int = 1, bet_size: int = 1):
        self.ante = ante
        self.bet_size = bet_size
        self.cards = [Card.JACK, Card.QUEEN, Card.KING]
    
    def get_deck(self) -> List[Card]:
        """Return a shuffled deck"""
        deck = self.cards.copy()
        random.shuffle(deck)
        return deck


class GameState:
    """Represents the current state of a Kuhn Poker game"""
    def __init__(self, config: GameConfig, cards: List[Card], history: str = ""):
        self.config = config
        self.cards = cards  # cards[0] for player 0, cards[1] for player 1
        self.history = history
        self.pot = 2 * config.ante  # Both players ante
    
    def is_terminal(self) -> bool:
        """Check if the game state is terminal"""
        # Showdown after both check
        if self.history == "cc":
            return True
        # Player 1 folds after Player 0 bets
        if self.history == "bf":
            return True
        # Player 0 folds after Player 0 checks and Player 1 bets
        if self.history == "cbf":
            return True
        # Showdown after call
        if self.history == "bc" or self.history == "cbc":
            return True
        return False
    
    def get_payoff(self, player: int) -> float:
        """Get the payoff for a player at a terminal state"""
        if not self.is_terminal():
            raise ValueError("Cannot get payoff at non-terminal state")
        
        if self.history == "cc":
            # Both checked - showdown
            if self.cards[0] > self.cards[1]:
                return self.config.ante if player == 0 else -self.config.ante
            else:
                return -self.config.ante if player == 0 else self.config.ante
        
        elif self.history == "bf":
            # Player 0 bet, Player 1 folded
            return self.config.ante if player == 0 else -self.config.ante
        
        elif self.history == "cbf":
            # Player 0 checked, Player 1 bet, Player 0 folded
            return -self.config.ante if player == 0 else self.config.ante
        
        elif self.history == "bc":
            # Player 0 bet, Player 1 called - showdown
            total = self.config.ante + self.config.bet_size
            if self.cards[0] > self.cards[1]:
                return total if player == 0 else -total
            else:
                return -total if player == 0 else total
        
        elif self.history == "cbc":
            # Player 0 checked, Player 1 bet, Player 0 called - showdown
            total = self.config.ante + self.config.bet_size
            if self.cards[0] > self.cards[1]:
                return total if player == 0 else -total
            else:
                return -total if player == 0 else total
        
        return 0.0
    
    def get_current_player(self) -> int:
        """Get the player who acts next"""
        if len(self.history) == 0 or len(self.history) == 2:
            return 0
        else:
            return 1
    
    def get_legal_actions(self) -> List[Action]:
        """Get legal actions for the current state"""
        if self.is_terminal():
            return []
        
        if len(self.history) == 0:
            # First action: Player 0 can check or bet
            return [Action.CHECK, Action.BET]
        
        elif len(self.history) == 1:
            if self.history[0] == 'c':
                # Player 0 checked: Player 1 can check or bet
                return [Action.CHECK, Action.BET]
            else:  # history[0] == 'b'
                # Player 0 bet: Player 1 can fold or call
                return [Action.FOLD, Action.CALL]
        
        elif len(self.history) == 2:
            if self.history == "cb":
                # Player 0 checked, Player 1 bet: Player 0 can fold or call
                return [Action.FOLD, Action.CALL]
        
        return []
    
    def apply_action(self, action: Action) -> 'GameState':
        """Create a new state by applying an action"""
        action_char = self._action_to_char(action)
        new_history = self.history + action_char
        return GameState(self.config, self.cards, new_history)
    
    def get_info_set(self, player: int) -> str:
        """Get the information set string for a player"""
        # Information set includes player's card and action history
        card_name = self.cards[player].name[0]  # J, Q, or K
        return f"{card_name}{self.history}"
    
    @staticmethod
    def _action_to_char(action: Action) -> str:
        """Convert action to character for history string"""
        if action == Action.CHECK:
            return 'c'
        elif action == Action.BET:
            return 'b'
        elif action == Action.FOLD:
            return 'f'
        elif action == Action.CALL:
            return 'c'
        return ''

