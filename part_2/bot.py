from takpy import Color, Game, Move, MoveKind, Piece
from collections.abc import Iterable

# Helper types
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


def road_piece(piece: Piece | None) -> bool:
    return piece == Piece.Flat or piece == Piece.Cap


def count_road_pieces(stacks: Iterable[None | Stack], color: Color) -> int:
    """Count how many stacks have a road piece with our color on top."""
    only_stacks = (stack for stack in stacks if stack is not None)
    return sum(
        road_piece(piece) for piece, colors in only_stacks if colors[-1] == color
    )


def columns(board: Board) -> Board:
    """Get the columns of a board."""
    return [[row[i] for row in board] for i in range(len(board[0]))]


def row_score(board: Board, color: Color) -> list[int]:
    """Count the road pieces per row."""
    return [count_road_pieces(row, color) for row in board]


def col_score(board: Board, color: Color) -> list[int]:
    """Count the road pieces per column."""
    return [count_road_pieces(col, color) for col in columns(board)]


def neighbor_stacks(board: Board, size: int, row: int, col: int) -> list[Stack]:
    """Get the neighboring stacks to a square."""
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
    """Get the Manhattan distance from the center."""
    mid = (size - 1) / 2
    return abs(row - mid) + abs(col - mid)


def winning_move(game: Game, moves: list[Move]) -> Move | None:
    """Return a winning move if there is one."""
    for move in moves:
        after_move = game.clone_and_play(move)
        if after_move.result().color() == game.to_move:
            return move
    return None


def move_kind_bonus(kind: MoveKind, distance: float) -> float:
    """Get the move score bonus based on the move kind."""
    match kind:
        case MoveKind.Place:
            return PLACEMENT - CENTER_PLACEMENT * distance
        case MoveKind.Spread:
            return SPREAD


def piece_type_bonus(
    piece: Piece | None, opp_color: Color, neighbors: list[Stack]
) -> float:
    """Get the move score bonus based on the piece type."""
    match piece:
        case Piece.Flat:
            return FLAT
        case Piece.Cap:
            score = CAP
            for _piece, colors in neighbors:
                if colors[-1] == opp_color:
                    score += CAP_NEXT_TO_OPPONENT_STACK * len(colors)
            return score
        case Piece.Wall:
            return WALL
        case None:
            return 0


def move_ordering(game: Game) -> list[Move]:
    """Return an ordering of the possible moves from best to worst."""
    board = game.board()
    my_color, opp_color = game.to_move, game.to_move.next()
    # Precompute row and column scores.
    my_row_score = row_score(board, game.to_move)
    my_col_score = col_score(board, game.to_move)

    def move_score(move: Move) -> float:
        """Give each move a score. Larger is better."""
        score = 0
        row, column = move.square
        distance = distance_from_center(row, column, game.size)
        neighbors = neighbor_stacks(board, game.size, row, column)
        score += move_kind_bonus(move.kind, distance)
        score += piece_type_bonus(move.piece, opp_color, neighbors)
        if road_piece(move.piece):
            score += ROW_COLUMN_ROAD * (my_row_score[row] + my_col_score[column])
        return score

    possible_moves = game.possible_moves()
    return sorted(possible_moves, key=move_score, reverse=game.ply >= 2)


def bot_move(game: Game) -> Move:
    """Pick a move automatically."""
    sorted_moves = move_ordering(game)
    best_move = sorted_moves[0]

    possibly_winning = winning_move(game, sorted_moves)
    if possibly_winning is not None:
        # Take immediate wins.
        best_move = possibly_winning
    else:
        # Look for the first non-losing move.
        for my_move in sorted_moves:
            after_my_move = game.clone_and_play(my_move)
            if after_my_move.result().color() == after_my_move.to_move:
                continue  # I made a road for the opponent accidentally.
            if winning_move(after_my_move, move_ordering(after_my_move)) is None:
                best_move = my_move
                break

    print(f"the bot played {best_move}")
    return best_move
