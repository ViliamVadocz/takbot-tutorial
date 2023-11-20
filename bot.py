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


def eval(game: Game) -> float:
    """Evaluate the board position. Positive outputs mean good for white, negative outputs mean good for black. Zero means draw."""
    match game.result:
        case GameResult.WhiteWin:
            return inf
        case GameResult.BlackWin:
            return -inf
        case GameResult.Draw:
            return 0

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


def move_rank(game: Game, move: Move) -> int:
    """Evaluate a move in the current position. Higher outputs mean the move is better."""
    board = game.board
    (row, col) = move.square

    score = 0
    # Rank central moves higher.
    score -= 10 * abs(row - (game.size - 1) / 2)
    score -= 10 * abs(col - (game.size - 1) / 2)

    if move.kind == MoveKind.Place:
        # Reward placements.
        score += 100
        # Rank flat placement above all others.
        if move.piece == Piece.Flat:
            score += 100

        # Reward placing next to pieces of the same color.
        if is_color(board, row - 1, col, game.to_move):
            score += 20
        if is_color(board, row + 1, col, game.to_move):
            score += 20
        if is_color(board, row, col - 1, game.to_move):
            score += 20
        if is_color(board, row, col + 1, game.to_move):
            score += 20
    else:
        # Rank spreads with flats on top lower
        top = game.board[row][col][-1]
        if top == Piece.Flat:
            score -= 100

    # In the first two plies we are placing the opponents piece, so we reverse the score.
    if game.ply < 2:
        return -score
    return score


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


def bot_move(game: Game):
    # Find out which moves are possible.
    moves = game.possible_moves
    # Sort the moves according to our `move_rank` function.
    moves.sort(key=lambda move: move_rank(game, move), reverse=True)

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


def main():
    game = new_game(6, 4)
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
