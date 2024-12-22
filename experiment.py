from math import inf
from takpy import (
    new_game,
    Color,
    GameResult,
    Game,
    Move,
    Piece,
    MoveKind,
)

# Type hints
Square = None | tuple[Piece, list[Color]]
Board = list[list[Square]]


def game_eval(game: Game) -> float:
    """Evaluate the board position. Positive outputs mean good for white, negative outputs mean good for black. Zero means draw."""
    match game.result:
        case GameResult.WhiteWin:
            return inf
        case GameResult.BlackWin:
            return -inf
        case GameResult.Draw:
            return 0

    # TODO: Improve this a lot, using ideas from move_ordering
    return (
        calculate_fcd(game)
        + unique_rows_and_cols(game, Color.White)
        - unique_rows_and_cols(game, Color.Black)
    )


def calculate_fcd(game: Game) -> int:
    fcd = -game.half_komi / 2
    for row in game.board:
        for square in row:
            if square is None:
                continue
            piece, colors = square
            if piece == Piece.Flat:
                match colors[-1]:
                    case Color.White:
                        fcd += 1
                    case Color.Black:
                        fcd -= 1
    return fcd


def unique_rows_and_cols(game: Game, color: Color) -> int:
    rows = 0
    for row in game.board:
        for square in row:
            if square is None:
                continue
            _piece, colors = square
            if colors[-1] == color:
                rows += 1
                break
    columns = 0
    for col in ((row[i] for row in game.board) for i in range(game.size)):
        for square in col:
            if square is None:
                continue
            _piece, colors = square
            if colors[-1] == color:
                columns += 1
                break
    return rows + columns


def cols(board: Board, size: int) -> Board:
    return [[row[i] for row in board] for i in range(size)]


def row_col_score(board: Board, size: int, color: Color) -> tuple[list[int], list[int]]:
    row_score = [
        sum(
            road_piece(square[0]) and square[1][-1] == color
            for square in row
            if square is not None
        )
        for row in board
    ]
    col_score = [
        sum(
            road_piece(square[0]) and square[1][-1] == color
            for square in col
            if square is not None
        )
        for col in cols(board, size)
    ]
    return row_score, col_score


def road_piece(piece: Piece) -> bool:
    match piece:
        case Piece.Flat | Piece.Cap:
            return True
        case Piece.Wall:
            return False


def neighbor_stacks(board: Board, size: int, row: int, col: int) -> list[Square]:
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


PLACEMENT_VALUE = 100
FLAT_VALUE = 100
CAP_VALUE = 50
WALL_VALUE = 0
ROAD_MOTIVATION = 10
CENTER_PRIORITY = 20
OPPONENT_NEXT_TO_NOBLE = 50
STACK_NEXT_TO_NOBLE = 10
FLAT_CAPTURE_PUNISHMENT = 100
SPREAD_ME_BONUS = 20


def move_ordering(game: Game) -> list[Move]:
    possible_moves = game.possible_moves
    me = game.to_move
    opponent = me.next()
    board = game.board
    row_score, col_score = row_col_score(board, game.size, me)

    def move_rank(move: Move) -> float:
        row, col = move.square
        distance_to_center = abs(row - (game.size + 1) / 2) + abs(
            col - (game.size + 1) / 2
        )
        neighbors = neighbor_stacks(board, game.size, row, col)
        score = 0
        match move.kind:
            case MoveKind.Place:
                score += PLACEMENT_VALUE
                # Road rewards
                match move.piece:
                    case Piece.Flat | Piece.Cap:
                        score += ROAD_MOTIVATION * (row_score[row] + col_score[col])
                        score -= CENTER_PRIORITY * distance_to_center
                # Noble rewards
                match move.piece:
                    case Piece.Cap | Piece.Wall:
                        for n in neighbors:
                            if n[1][-1] == opponent:
                                score += OPPONENT_NEXT_TO_NOBLE
                            score += STACK_NEXT_TO_NOBLE * len(n[1])
                # Piece-type bonus
                match move.piece:
                    case Piece.Flat:
                        score += FLAT_VALUE
                    case Piece.Cap:
                        score += CAP_VALUE
                    case Piece.Wall:
                        score += WALL_VALUE
            case MoveKind.Spread:
                stack = board[row][col]
                piece, colors = stack
                # Punish flat captures
                if piece == Piece.Flat:
                    score -= FLAT_CAPTURE_PUNISHMENT
                # Reward dropping our color on top
                dropped = 0
                for drop_count in move.drop_counts[:-1]:
                    dropped += drop_count
                    if colors[dropped - 1] == me:
                        score += SPREAD_ME_BONUS
        return score

    return sorted(game.possible_moves, key=move_rank, reverse=game.ply > 1)


def is_color(
    board: list[list[None | tuple[Piece, list[Color]]]],
    row: int,
    col: int,
    color: Color,
) -> bool:
    try:
        square = board[row][col]
        return square is not None and square[1][-1] == color
    except IndexError:
        return False


def pretty_print(game: Game):
    print(game)
    for i, row in list(enumerate(game.board, 1))[::-1]:
        print(i, end=" ")
        for square in row:
            if square is None:
                print("🔳", end=" ")
                continue
            match square:
                case (Piece.Flat, [*_, Color.White]):
                    print("🟧", end=" ")
                case (Piece.Wall, [*_, Color.White]):
                    print("🔶", end=" ")
                case (Piece.Cap, [*_, Color.White]):
                    print("🟠", end=" ")
                case (Piece.Flat, [*_, Color.Black]):
                    print("🟦", end=" ")
                case (Piece.Wall, [*_, Color.Black]):
                    print("🔷", end=" ")
                case (Piece.Cap, [*_, Color.Black]):
                    print("🔵", end=" ")
        print()
    print("   a  b  c  d  e  f  g  h"[: 1 + game.size * 3])


def player_move(game: Game):
    while True:
        move = input("your move: ")
        try:
            game.play(Move.from_ptn(move))
            break
        except Exception as e:
            print(e)


# https://en.wikipedia.org/wiki/Negamax
def negamax(game: Game, depth: int) -> float:
    match game.result:
        case GameResult.WhiteWin:
            return inf
        case GameResult.BlackWin:
            return -inf
        case GameResult.Draw:
            return 0.0
    if depth == 0:
        return game_eval(game)
    if game.to_move == Color.White:
        for move in game.possible_moves:
            clone = game.clone()
            clone.play(move)
            value = max(value, negamax(clone, depth - 1))
    else:
        for move in game.possible_moves:
            clone = game.clone()
            clone.play(move)
            value = min(value, negamax(clone, depth - 1))
    return value


# https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning
def alpha_beta(game: Game, depth: int, alpha: float = -inf, beta: float = inf) -> float:
    match game.to_move, game.result:
        case GameResult.WhiteWin:
            return inf
        case GameResult.BlackWin:
            return -inf
        case GameResult.Draw:
            return 0.0
    if depth == 0:
        return game_eval(game)

    moves = move_ordering(game)
    if game.to_move == Color.White:
        value = -inf
        for move in moves:
            search_value = alpha_beta(game.clone_and_play(move), depth - 1, alpha, beta)
            value = max(value, search_value)
            if value > beta:
                break  # beta cutoff
            alpha = max(alpha, beta)
        return value

    else:
        value = inf
        for move in moves:
            search_value = alpha_beta(game.clone_and_play(move), depth - 1, alpha, beta)
            value = min(value, search_value)
            if value < alpha:
                break  # alpha cutoff
            beta = min(beta, value)


def bot_move(game: Game):
    moves = move_ordering(game)

    # Find out which move gives the best evaluation.
    # We do this by trying each move in turn and comparing the static evaluations.
    best_eval = -inf
    best_move = moves[0]
    for move in moves:
        # Create a clone of the game and try playing the move.
        copy = game.clone()
        copy.play(move)
        # Evaluate the position afterwards.
        current_eval = eval(copy)
        # The evaluation is from white's perspective, so we need to flip it when black.
        if game.to_move == Color.Black:
            current_eval = -current_eval
        # If the current evaluation is better than the previous best, this move must be better.
        if current_eval > best_eval:
            best_move = move
            best_eval = current_eval
    print("bot move:", best_move, "with eval", best_eval)
    game.play(best_move)


def bot_move_old(game: Game):
    moves = move_ordering(game)

    # Find out which move gives the best evaluation.
    # We do this by trying each move in turn and comparing the static evaluations.
    best_eval = -inf
    best_move = moves[0]
    for move in moves:
        # Create a clone of the game and try playing the move.
        copy = game.clone()
        copy.play(move)
        # Evaluate the position afterwards.
        current_eval = eval(copy)
        # The evaluation is from white's perspective, so we need to flip it when black.
        if game.to_move == Color.Black:
            current_eval = -current_eval
        # If the current evaluation is better than the previous best, this move must be better.
        if current_eval > best_eval:
            best_move = move
            best_eval = current_eval
    print("bot move:", best_move, "with eval", best_eval)
    game.play(best_move)


SIZE = 6
KOMI = 2
HALF_KOMI = int(KOMI * 2)


def main():
    game = new_game(SIZE, HALF_KOMI)
    player_color = Color.White

    pretty_print(game)
    while game.result == GameResult.Ongoing:
        if game.to_move == player_color:
            player_move(game)
        else:
            bot_move(game)
        pretty_print(game)

    match game.result:
        case GameResult.WhiteWin:
            print("🟧 wins!")
        case GameResult.BlackWin:
            print("🟦 wins!")
        case GameResult.Draw:
            print("It's a draw!")


if __name__ == "__main__":
    main()
