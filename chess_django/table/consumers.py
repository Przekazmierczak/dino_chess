import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from .models import Game, Board
from . import pieces

class TableConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.table_id = self.scope["url_route"]["kwargs"]["table_id"]
        self.table_group_id = "table_%s" % self.table_id

        # Join room group
        await self.channel_layer.group_add(self.table_group_id, self.channel_name)

        await self.accept()

        await self.send_current_state()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.table_group_id, self.channel_name)

    # Connect to the page
    async def send_current_state(self):
        current_game = await self.get_game_from_database()
        user_name = self.scope["user"].username

        white_player_name = current_game.white.username if current_game.white else "Player 1"
        black_player_name = current_game.black.username if current_game.black else "Player 2"

        # Game already started
        if current_game.white_ready and current_game.black_ready:
            current_state = await self.get_board_from_database(current_game)
            winner = {"w": "white", "b": "black"}.get(current_game.winner, "draw") if current_game.winner else None
            turn, total_moves, soft_moves = current_state.turn, current_state.total_moves, current_state.soft_moves
            current_board_json = json.loads(current_state.board)

            # Current player
            if ((current_state.turn == "white" and str(current_game.white) == user_name) or (current_state.turn == "black" and str(current_game.black) == user_name) and not winner):
                board, _, checking = pieces.Board(current_board_json, current_state.turn, current_state.castling, current_state.enpassant).create_json_class()
            # Rest
            else:
                board = pieces.boardSimplify(current_board_json)
                checking = None

        # Start board
        else:
            board = pieces.boardSimplify(None)
            winner, turn, checking, total_moves, soft_moves =  None, None, None, 0, 0
        
        await self.send(text_data=json.dumps({
            "user": user_name,
            "white_player": white_player_name,
            "black_player": black_player_name,
            "white_player_ready": current_game.white_ready,
            "black_player_ready": current_game.black_ready,
            "winner": winner,
            "board": board,
            "turn": turn,
            "checking": checking,
            "total_moves": total_moves,
            "soft_moves": soft_moves
            }))

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        current_game = await self.get_game_from_database()
        user = self.scope["user"]

        # Game already started - player made a move
        if text_data_json["move"]:
            move = text_data_json["move"]
            promotion = text_data_json["promotion"]

            prev_state = await self.get_board_from_database(current_game)
            prev_boards = await self.get_prev_board_from_database(current_game)

            prev_board = json.loads(prev_state.board)

            white_player_name = current_game.white.username
            black_player_name = current_game.black.username

            next_board, next_castling, next_enpassant, soft_move = pieces.Board(prev_board, prev_state.turn, prev_state.castling, prev_state.enpassant).create_new_json_board(move, promotion)
            turn = "black" if prev_state.turn == "white" else "white"
            total_moves = prev_state.total_moves + 1 if turn == "white" else prev_state.total_moves
            soft_moves = prev_state.soft_moves + 1 if soft_move else 0

            if next_board and ((prev_state.turn == "white" and white_player_name == str(user)) or (prev_state.turn == "black" and black_player_name == str(user))):
                board, winner, checking = pieces.Board(next_board, turn, next_castling, next_enpassant).create_json_class()

                # Threefold repetition
                repetition = 1
                next_turn_short = "w" if turn == "white" else "b"
                for prev_board in prev_boards:
                    if (prev_board.board, prev_board.turn, prev_board.castling, prev_board.enpassant) == (json.dumps(next_board), next_turn_short, next_castling, next_enpassant):
                        repetition += 1
                    if repetition >= 3:
                        winner = "draw"
                        break

                # 50 move rule
                if soft_moves == 100:
                    winner = "draw"

                await self.push_new_board_to_database(next_board, turn, next_castling, next_enpassant, winner, total_moves, soft_moves)
            else:
                # Add disconnect
                pass
        
        # Game not started yet - user join the table
        else:
            await self.push_players_state_to_db(current_game, user, text_data_json)

            white_player_name = current_game.white.username if current_game.white else "Player 1"
            black_player_name = current_game.black.username if current_game.black else "Player 2"

            # Game already started
            if current_game.white_ready and current_game.black_ready:
                current_state = await self.get_board_from_database(current_game)
                current_board_json = json.loads(current_state.board)
                board, winner, checking = pieces.Board(current_board_json, current_state.turn, current_state.castling, current_state.enpassant).create_json_class()
                turn, total_moves, soft_moves = current_state.turn, current_state.total_moves, current_state.soft_moves
            # Start board
            else:
                board = pieces.boardSimplify(None)
                winner, turn, checking, total_moves, soft_moves =  None, None, None, 0, 0

        # Send message to room group
        await self.channel_layer.group_send(
            self.table_group_id, {
                "type": "new_board",
                "white_player": white_player_name,
                "black_player": black_player_name,
                "white_player_ready": current_game.white_ready,
                "black_player_ready": current_game.black_ready,
                "winner": winner,
                "board": board,
                "turn": turn,
                "checking": checking,
                "total_moves": total_moves,
                "soft_moves": soft_moves
                }
        )

    # Receive message from room group
    async def new_board(self, event):
        user_name = self.scope["user"].username

        white_player = event["white_player"]
        black_player = event["black_player"]
        white_player_ready = event["white_player_ready"]
        black_player_ready = event["black_player_ready"]
        winner = event["winner"]
        board = event["board"]
        turn = event["turn"]
        checking = event["checking"]
        total_moves = event["total_moves"]
        soft_moves = event["soft_moves"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "user": user_name,
            "white_player": white_player,
            "black_player": black_player,
            "white_player_ready": white_player_ready,
            "black_player_ready": black_player_ready,
            "winner": winner,
            "board": board,
            "turn": turn,
            "checking": checking,
            "total_moves": total_moves,
            "soft_moves": soft_moves
            }))
        
    @sync_to_async
    def get_game_from_database(self):
        current_game = Game.objects.get(pk=self.table_id)
        _, _ = current_game.white, current_game.black
        return current_game
    
    @sync_to_async
    def get_board_from_database(self, game):
        current_board = Board.objects.filter(game=game).latest('id')
        current_board.turn = "white" if current_board.turn == "w" else "black"
        return current_board

    @sync_to_async
    def get_prev_board_from_database(self, game):
        prev_boards_db = Board.objects.filter(game=game)
        prev_boards = list(prev_boards_db)
        return prev_boards
    
    @sync_to_async
    def push_new_board_to_database(self, updated_board, turn, castling, enpassant, winner, total_moves, self_moves):
        game = Game.objects.get(pk=self.table_id)
        if winner:
            db_winner = {"white": "w", "black": "b"}.get(winner, "d")
            game.winner = db_winner
            game.save()

        db_turn = "w" if turn == "white" else "b"

        Board.objects.create(
            game = game,
            total_moves = total_moves,
            board = json.dumps(updated_board),
            turn = db_turn,
            castling = castling,
            enpassant = enpassant,
            soft_moves = self_moves
        )

    @sync_to_async
    def push_players_state_to_db(self, game, user, text_data_json):
        # push player to database
        if text_data_json["white_player"]:
            game.white = user
        elif text_data_json["black_player"]:
            game.black = user
        # remove player from database
        elif text_data_json["white_player"] == False:
            game.white = None
        elif text_data_json["black_player"] == False:
            game.black = None
        # push player ready to database
        elif text_data_json["white_player_ready"]:
            game.white_ready = True
        elif text_data_json["black_player_ready"]:
            game.black_ready = True
        # remove player from database
        elif text_data_json["white_player_ready"] == False:
            game.white_ready = False
        elif text_data_json["black_player_ready"] == False:
            game.black_ready = False

        # create new board
        if game.white_ready and game.black_ready:
            starting_board = [["R", "N", "B", "K", "Q", "B", "N", "R"],
                              ["P", "P", "P", "P", "P", "P", "P", "P"],
                              [" ", " ", " ", " ", " ", " ", " ", " "],
                              [" ", " ", " ", " ", " ", " ", " ", " "],
                              [" ", " ", " ", " ", " ", " ", " ", " "],
                              [" ", " ", " ", " ", " ", " ", " ", " "],
                              ["p", "p", "p", "p", "p", "p", "p", "p"],
                              ["r", "n", "b", "k", "q", "b", "n", "r"]]
            Board.objects.create(
                game = game,
                total_moves = 0,
                board = json.dumps(starting_board),
                turn = "w",
                castling = "KQkq",
                enpassant = "__",
                soft_moves = 0
            )
        game.save()