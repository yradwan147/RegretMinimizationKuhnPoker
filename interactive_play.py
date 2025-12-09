"""
Interactive Kuhn Poker player - Play against the trained CFR strategy.
"""
import random
from kuhn_poker import GameConfig, GameState, Card, Action
from cfr import CFRTrainer
import numpy as np


class KuhnPokerGame:
    """Interactive Kuhn Poker game"""
    
    def __init__(self, trainer: CFRTrainer):
        self.trainer = trainer
        self.config = trainer.config
    
    def get_action_from_strategy(self, state: GameState, player: int) -> Action:
        """Get an action based on the learned strategy"""
        info_set_key = state.get_info_set(player)
        legal_actions = state.get_legal_actions()
        
        if info_set_key in self.trainer.info_sets:
            info_set = self.trainer.info_sets[info_set_key]
            strategy = info_set.get_average_strategy()
            
            # Sample action based on strategy
            action_idx = np.random.choice(len(legal_actions), p=strategy)
            return legal_actions[action_idx]
        else:
            # Uniform random if not seen
            return random.choice(legal_actions)
    
    def play_game(self, human_player: int = 0):
        """
        Play a single game.
        
        Args:
            human_player: Which player is human (0 or 1)
        """
        # Deal cards
        deck = self.config.get_deck()
        cards = [deck[0], deck[1]]
        
        print("\n" + "="*60)
        print("NEW GAME")
        print("="*60)
        print(f"Your card: {cards[human_player].name}")
        print(f"Pot: {2 * self.config.ante} chips (both antes)")
        print()
        
        state = GameState(self.config, cards)
        
        while not state.is_terminal():
            current_player = state.get_current_player()
            legal_actions = state.get_legal_actions()
            
            if current_player == human_player:
                # Human's turn
                action = self.get_human_action(state, legal_actions)
            else:
                # AI's turn
                action = self.get_action_from_strategy(state, current_player)
                action_name = action.name
                print(f"Opponent {action_name.lower()}s")
            
            state = state.apply_action(action)
            print()
        
        # Game over - show results
        print("="*60)
        print("GAME OVER")
        print("="*60)
        
        # Reveal opponent's card
        opponent_player = 1 - human_player
        print(f"Your card: {cards[human_player].name}")
        print(f"Opponent's card: {cards[opponent_player].name}")
        print()
        
        payoff = state.get_payoff(human_player)
        
        if payoff > 0:
            print(f"YOU WIN! +{int(payoff)} chips")
        elif payoff < 0:
            print(f"YOU LOSE! {int(payoff)} chips")
        else:
            print("TIE!")
        
        print("="*60)
        
        return payoff
    
    def get_human_action(self, state: GameState, legal_actions: list) -> Action:
        """Get action from human player"""
        print(f"Your card: {state.cards[0].name}")
        print(f"History: {state.history if state.history else '(start)'}")
        print(f"Pot: {state.pot + (state.history.count('b') * self.config.bet_size)} chips")
        print()
        print("Legal actions:")
        
        action_map = {}
        for i, action in enumerate(legal_actions):
            print(f"  {i + 1}. {action.name}")
            action_map[i + 1] = action
        
        while True:
            try:
                choice = input("\nYour choice (number): ")
                choice_num = int(choice)
                if choice_num in action_map:
                    return action_map[choice_num]
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("\nInvalid input. Please enter a number.")
    
    def play_session(self, num_games: int = 5, human_player: int = 0):
        """Play multiple games and track results"""
        print("\n" + "="*60)
        print("KUHN POKER - PLAY AGAINST CFR STRATEGY")
        print("="*60)
        print(f"\nYou are Player {human_player}")
        print(f"Playing {num_games} games")
        print("\nRules:")
        print("  - 3 cards: Jack (weakest), Queen, King (strongest)")
        print("  - Each player antes 1 chip")
        print("  - Check = pass, Bet = add 1 chip to pot")
        print("  - Fold = give up, Call = match bet and showdown")
        print()
        
        input("Press Enter to start...")
        
        total_payoff = 0
        wins = 0
        losses = 0
        ties = 0
        
        for game_num in range(num_games):
            print(f"\nGame {game_num + 1}/{num_games}")
            payoff = self.play_game(human_player)
            
            total_payoff += payoff
            if payoff > 0:
                wins += 1
            elif payoff < 0:
                losses += 1
            else:
                ties += 1
            
            if game_num < num_games - 1:
                input("\nPress Enter for next game...")
        
        # Final statistics
        print("\n" + "="*60)
        print("SESSION COMPLETE")
        print("="*60)
        print(f"\nGames played: {num_games}")
        print(f"Wins: {wins}")
        print(f"Losses: {losses}")
        print(f"Ties: {ties}")
        print(f"Total payoff: {int(total_payoff)} chips")
        print(f"Average payoff per game: {total_payoff / num_games:.2f} chips")
        print()
        
        if total_payoff > 0:
            print("Congratulations! You beat the AI!")
        elif total_payoff < 0:
            print("The AI won this session. The CFR strategy is tough to beat!")
        else:
            print("Perfectly even! Well played!")
        
        print("="*60)


def main():
    """Main function to run interactive game"""
    print("Loading CFR strategy...")
    
    # Train CFR strategy
    config = GameConfig(ante=1, bet_size=1)
    trainer = CFRTrainer(config)
    
    print("Training CFR (10000 iterations)...")
    trainer.train(10000)
    print("Training complete!\n")
    
    # Create game
    game = KuhnPokerGame(trainer)
    
    # Play session
    game.play_session(num_games=5, human_player=0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")

