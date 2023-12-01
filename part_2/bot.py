from takpy import GameResult, Move, Piece, Color, Game, MoveKind
from collections.abc import Iterable


Stack = tuple[Piece, list[Color]]
Board = list[list[None | Stack]]

PLACEMENT = 100
SPREAD = 0
FLAT = 100
CAP = 50
WALL = 0
ROW_COLUMN_ROAD = 10
CAP_NEXT_TO_OPPONENT_STACK = 50
CENTER_PLACEMENT = 10


def move_ordering(game: Game) -> list[Move]:
    """Return a list of possible moves in the game, sorted with the best moves at the start."""
    board = game.board
    my_color = game.to_move
    opp_color = game.to_move.next()
    my_row_score = row_score(board, my_color)
    my_col_score = col_score(board, my_color)

    def move_score(move: Move) -> float:
        score = 0
        row, column = move.square
        neighbors = neighbor_stacks(board, game.size, row, column)
        distance = distance_from_center(row, column, game.size)
        match move.kind:
            case MoveKind.Place:
                score += PLACEMENT
                score -= CENTER_PLACEMENT * distance
            case MoveKind.Spread:
                score += SPREAD
        match move.piece:
            case Piece.Flat:
                score += FLAT
            case Piece.Cap:
                score += CAP
                for _piece, colors in neighbors:
                    if colors[-1] == opp_color:
                        score += CAP_NEXT_TO_OPPONENT_STACK * len(colors)
            case Piece.Wall:
                score += WALL
        if road_piece(move.piece):
            score += ROW_COLUMN_ROAD * (my_row_score[row] + my_col_score[column])
        return score

    moves = game.possible_moves
    return sorted(moves, key=move_score, reverse=game.ply > 1)


def road_piece(piece: Piece) -> bool:
    return piece == Piece.Flat or piece == Piece.Cap


def noble_piece(piece: Piece) -> bool:
    return piece == Piece.Cap or piece == Piece.Wall


def count_road_pieces(stacks: Iterable[None | Stack], color: Color) -> int:
    only_stacks = (stack for stack in stacks if stack is not None)
    return sum(
        road_piece(piece) for piece, colors in only_stacks if colors[-1] == color
    )


def columns(board: Board) -> Board:
    return [[row[i] for row in board] for i in range(len(board[0]))]


def row_score(board: Board, color: Color) -> list[int]:
    return [count_road_pieces(row, color) for row in board]


def col_score(board: Board, color: Color) -> list[int]:
    return [count_road_pieces(col, color) for col in columns(board)]


def neighbor_stacks(board: Board, size: int, row: int, col: int) -> list[Stack]:
    neighbors = []
    if row < size - 1:
        neighbors.append(board[row + 1][col])
    if row >= 1:
        neighbors.append(board[row - 1][col])
    if col < size - 1:
        neighbors.append(board[row][col + 1])
    if col >= 1:
        neighbors.append(board[row][col - 1])
    return [n for n in neighbors if n is not None]


def distance_from_center(row: int, col: int, size: int) -> float:
    mid = (size - 1) / 2
    return abs(row - mid) + abs(col - mid)


def winning_move(game: Game, moves: list[Move]) -> Move | None:
    """Get the winning move from the list of moves, if there is one."""
    for move in moves:
        after_move = game.clone_and_play(move)
        if after_move.result.color() == game.to_move:
            return move
    return None


def bot_move(game: Game):
    moves = move_ordering(game)
    best_move = moves[0]

    possibly_winning = winning_move(game, moves)
    if possibly_winning is not None:
        # Take immediate wins.
        best_move = possibly_winning
    else:
        # Look for the first non-losing move.
        for my_move in moves:
            after_my_move = game.clone_and_play(my_move)
            if after_my_move.result.color() == after_my_move.to_move:
                continue  # I made a road for the opponent accidentally.
            if winning_move(after_my_move, move_ordering(after_my_move)) is None:
                best_move = my_move
                break

    print(f"the bot played {best_move}")
    game.play(best_move)
