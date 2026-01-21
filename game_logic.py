import random
from typing import List, Optional, Dict

class Tile:
    def __init__(self, suit: str, value: int, is_red: bool = False):
        self.suit = suit
        self.value = value
        self.is_red = is_red

    def __repr__(self):
        return f"{self.suit}{self.value}{'r' if self.is_red else ''}"

    def to_dict(self):
        return {"suit": self.suit, "value": self.value, "is_red": self.is_red}

    def __eq__(self, other):
        if not isinstance(other, Tile): return False
        return self.suit == other.suit and self.value == other.value and self.is_red == other.is_red

    def __lt__(self, other):
        suits_order = {'man': 0, 'pin': 1, 'sou': 2, 'honors': 3}
        if suits_order[self.suit] != suits_order[other.suit]:
            return suits_order[self.suit] < suits_order[other.suit]
        return self.value < other.value

class Deck:
    def __init__(self):
        self.tiles: List[Tile] = []
        self._initialize_deck()

    def _initialize_deck(self):
        self.tiles = []
        for suit in ['man', 'pin', 'sou']:
            for value in range(1, 10):
                for _ in range(4):
                    self.tiles.append(Tile(suit, value))
        for value in range(1, 8):
            for _ in range(4):
                self.tiles.append(Tile('honors', value))

    def shuffle(self):
        random.shuffle(self.tiles)

    def draw(self) -> Optional[Tile]:
        if not self.tiles: return None
        return self.tiles.pop()

class Player:
    def __init__(self, name: str, session_id: str):
        self.name = name
        self.session_id = session_id
        self.hand: List[Tile] = []
        self.discards: List[Tile] = []
        self.score = 25000
        self.wind = 0 # 0:East, 1:South, 2:West, 3:North (Relative to dealer)
        self.is_riichi = False

    def draw_tile(self, tile: Tile):
        self.hand.append(tile)

    def discard_tile(self, tile_index: int) -> Optional[Tile]:
        if 0 <= tile_index < len(self.hand):
            tile = self.hand.pop(tile_index)
            self.discards.append(tile)
            self.sort_hand()
            return tile
        return None

    def sort_hand(self):
        self.hand.sort()

class MahjongGame:
    def __init__(self):
        self.players: List[Player] = []
        self.deck = Deck()
        self.turn_index = 0 # Index of player whose turn it is
        self.dealer_index = 0 # Index of dealer (East)
        self.round_wind = '東' # Default to Japanese
        self.round_number = 1
        self.honba = 0
        self.pot = 0
        self.dora_indicators: List[Tile] = []
        self.dead_wall: List[Tile] = [] # Wangpai
        self.game_started = False

    def add_player(self, player: Player) -> bool:
        if len(self.players) < 4:
            self.players.append(player)
            return True
        return False

    def start_dealer_selection(self):
        """
        Rolls dice for 4 players to decide the dealer.
        Returns the dice results and the index of the dealer.
        """
        if len(self.players) < 4: return None
        
        # 1. Roll for everyone
        rolls = []
        for _ in self.players:
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            rolls.append({'d1': d1, 'd2': d2, 'total': d1 + d2})
        
        # 2. Find winner (highest total)
        # In case of tie, simple tie-breaker: first one wins (simplified)
        max_val = -1
        dealer_idx = 0
        for i, r in enumerate(rolls):
            if r['total'] > max_val:
                max_val = r['total']
                dealer_idx = i
        
        self.dealer_index = dealer_idx
        self.turn_index = self.dealer_index
        
        # 3. Assign Winds
        # Dealer is East (0), next is South (1), etc.
        # Wind = (PlayerIdx - DealerIdx) % 4
        # Note: Internal p.wind is int 0..3, mapped to char in frontend.
        # self.round_wind is string displayed directly.
        
        self.round_wind = '東'
        
        return {
            'rolls': rolls,
            'dealer_index': dealer_idx,
            'dealer_name': self.players[dealer_idx].name
        }

    def start_game(self):
        # Called AFTER dealer selection
        if len(self.players) == 4:
            self.deck.shuffle()
            # Setup Dead Wall (14 tiles)
            self.dead_wall = [self.deck.draw() for _ in range(14)]
            # Dora Indicator
            self.dora_indicators = [self.dead_wall[0]] 
            
            # Deal Hands
            self.deal_initial_hands()
            # Turn starts with Dealer
            self.turn_index = self.dealer_index
            self.game_started = True
            return True
        return False

    def deal_initial_hands(self):
        for _ in range(13):
            for player in self.players:
                tile = self.deck.draw()
                if tile: player.draw_tile(tile)
        for player in self.players:
            player.sort_hand()

    def get_current_player(self) -> Player:
        return self.players[self.turn_index]

    def player_discard(self, session_id: str, tile_index: int) -> Optional[dict]:
        current_player = self.get_current_player()
        if current_player.session_id != session_id: return None

        discarded_tile = current_player.discard_tile(tile_index)
        if discarded_tile:
            # Check wins/calls here (PON/CHI/RON) - Simplified: none for now, straight to next
            
            self.turn_index = (self.turn_index + 1) % 4
            next_player = self.get_current_player()
            drawn_tile = self.deck.draw()
            
            if drawn_tile:
                next_player.draw_tile(drawn_tile)
            else:
                # Ryuukyoku (Exhaustive Draw)
                pass 

            return {
                "discarded": discarded_tile.to_dict(),
                "next_player": next_player.name,
                "next_player_sid": next_player.session_id,
                "drawn_tile": drawn_tile.to_dict() if drawn_tile else None,
                "remaining_tiles": len(self.deck.tiles)
            }
        return None

    def get_public_state(self):
        return {
             "game_started": self.game_started,
             "round_wind": self.round_wind,
             "round_number": self.round_number,
             "remaining_tiles": len(self.deck.tiles),
             "honba": self.honba,
             "pot": self.pot,
             "dora": [t.to_dict() for t in self.dora_indicators],
             "players": [{
                 "name": p.name,
                 "score": p.score,
                 "wind": p.wind,
                 "discards": [t.to_dict() for t in p.discards],
                 "is_riichi": p.is_riichi
             } for p in self.players]
        }
