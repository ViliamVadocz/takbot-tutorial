from takpy import new_game, GameResult, Move, Piece, Color, Game

from bot import bot_move


def cli():
    player_color = Color.White
    game = new_game(6)

    while game.result == GameResult.Ongoing:
        pretty_print(game)
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


def player_move(game: Game):
    while True:
        user_input = input("enter move: ")
        try:
            move = Move.from_ptn(user_input)
        except ValueError as error:
            print(f"invalid PTN: {error}")
            continue
        try:
            game.play(move)
            break  # valid move was entered and played
        except ValueError as error:
            print(f"invalid move: {error}")


def pretty_print(game: Game):
    # Print the TPS.
    print(game)
    # Print the board.
    for rank, row in reversed(list(enumerate(game.board, 1))):
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


if __name__ == "__main__":
    cli()
