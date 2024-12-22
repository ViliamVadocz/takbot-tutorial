from takpy import Color, Game, GameResult, Move, new_game, Piece
from bot import bot_move


def pretty_print(game: Game):
    # Print the TPS.
    print(game)
    # Print the board.
    for rank, row in reversed(list(enumerate(game.board(), 1))):
        print(rank, end=" ")
        for square in row:
            # If the square is empty, print the empty symbol.
            if square is None:
                print("🔳", end=" ")
                continue
            # Print a symbol for the top piece of each stack.
            piece, colors = square
            match colors[-1], piece:
                case Color.White, Piece.Flat:
                    print("🟧", end=" ")
                case Color.White, Piece.Wall:
                    print("🔶", end=" ")
                case Color.White, Piece.Cap:
                    print("🟠", end=" ")
                case Color.Black, Piece.Flat:
                    print("🟦", end=" ")
                case Color.Black, Piece.Wall:
                    print("🔷", end=" ")
                case Color.Black, Piece.Cap:
                    print("🔵", end=" ")
        # Print a newline after each row.
        print()
    # Print the files.
    print("   a  b  c  d  e  f  g  h"[: 1 + game.size * 3])


def player_move(game: Game) -> Move:
    while True:
        user_input = input("enter move: ")
        try:
            move = Move(user_input)  # type: ignore
        except ValueError as error:
            print(f"invalid PTN: {error}")
            continue
        try:
            game.clone_and_play(move)
            return move  # valid move was entered and played
        except ValueError as error:
            print(f"invalid move: {error}")


def cli():
    player_color = Color.White
    game = new_game(6)

    while game.result() == GameResult.Ongoing:
        pretty_print(game)
        if game.to_move == player_color:
            move = player_move(game)
        else:
            move = bot_move(game)
        game.play(move)

    # Summary after the game.
    pretty_print(game)
    match game.result:
        case GameResult.WhiteWin:
            print("🟧 wins!")
        case GameResult.BlackWin:
            print("🟦 wins!")
        case GameResult.Draw:
            print("It's a draw!")


if __name__ == "__main__":
    cli()
