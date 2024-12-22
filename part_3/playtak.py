import asyncio
from websockets.asyncio.client import connect, ClientConnection
from websockets import Subprotocol
from takpy import Color, Move, MoveKind, Piece, Direction, new_game, GameResult
from bot import bot_move


async def ping(ws: ClientConnection, stop_event: asyncio.Event):
    PERIOD_SECONDS = 30
    while not stop_event.is_set():
        await asyncio.sleep(PERIOD_SECONDS)
        await ws.send("PING")


def to_color(s: str) -> Color:
    match s:
        case "white":
            return Color.White
        case "black":
            return Color.Black
        case _:
            raise ValueError("invalid color")


async def wait_until_game_start(ws: ClientConnection) -> tuple[int, Color]:
    while True:
        msg = await ws.recv()
        assert isinstance(msg, bytes)  # subprotocol is "binary"
        match msg.decode().split():
            # Game Start 645331 6 Guest535 vs x57696c6c white 300 0 30 1 0 0
            case ["Game", "Start", game_id, _, _, "vs", _, color, *_]:
                return int(game_id), to_color(color)


def to_playtak_square(row: int, col: int) -> str:
    return "ABCDEFGH"[col] + str(row + 1)


def to_playtak_notation(move: Move) -> str:
    row, col = move.square
    start = to_playtak_square(row, col)
    match move.kind:
        case MoveKind.Place:
            piece = ""
            match move.piece:
                case Piece.Flat:
                    pass
                case Piece.Wall:
                    piece = " W"
                case Piece.Cap:
                    piece = " C"
            return f"P {start}{piece}"
        case MoveKind.Spread:
            drop_counts = move.drop_counts()
            assert drop_counts is not None
            end_row, end_col = row, col
            match move.direction:
                case Direction.Up:
                    end_row += len(drop_counts)
                case Direction.Down:
                    end_row -= len(drop_counts)
                case Direction.Left:
                    end_col -= len(drop_counts)
                case Direction.Right:
                    end_col += len(drop_counts)
            direction = move.direction
            end = to_playtak_square(end_row, end_col)
            drops = " ".join(str(x) for x in drop_counts)
            return f"M {start} {end} {drops}"


def from_playtak_notation(s: str) -> Move:
    match s.split():
        case ["P", square, *maybe_piece]:
            piece = ""
            match maybe_piece:
                case ["W"]:
                    piece = "S"
                case ["C"]:
                    piece = "C"
            return Move(piece + square.lower())  # type: ignore
        case ["M", start, end, *drops]:
            direction = ""
            match ord(end[0]) - ord(start[0]), ord(end[1]) - ord(start[1]):
                case x, y if x > 0:
                    direction = ">"
                case x, y if x < 0:
                    direction = "<"
                case x, y if y > 0:
                    direction = "+"
                case x, y if y < 0:
                    direction = "-"
            return Move(f"{sum(int(x) for x in drops)}{start.lower()}{direction}{"".join(drops)}")  # type: ignore
        case _:
            raise ValueError(f"unrecognized move: {s}")


async def wait_until_move(ws: ClientConnection, game_id: int) -> Move:
    while True:
        msg = await ws.recv()
        assert isinstance(msg, bytes)  # subprotocol is "binary"
        match msg.decode().strip().split(maxsplit=1):
            case [game, notation]:
                if game == f"Game#{game_id}" and notation.startswith(("P", "M")):
                    return from_playtak_notation(notation)


def seek(size: int, clock_seconds: int, increment_seconds: int) -> str:
    return f"Seek {size} {clock_seconds} {increment_seconds}"


async def talk_to_playtak():
    URI = "ws://playtak.com:9999/ws"
    subprotocols = [Subprotocol("binary")]
    async with connect(URI, subprotocols=subprotocols, ping_timeout=None) as ws:
        stop_event = asyncio.Event()
        ping_task = asyncio.create_task(ping(ws, stop_event))

        await ws.send("Login Guest")
        await ws.send(seek(6, 5 * 60, 5))

        game_id, my_color = await wait_until_game_start(ws)
        print(game_id, my_color)

        game = new_game(6)
        while game.result() == GameResult.Ongoing:
            if game.to_move == my_color:
                move = bot_move(game)
                await ws.send(f"Game#{game_id} {to_playtak_notation(move)}")
            else:
                move = await wait_until_move(ws, game_id)
            game.play(move)

        stop_event.set()
        print("Waiting for all background tasks to finish...")
        await ping_task

        await ws.send("quit")


if __name__ == "__main__":
    asyncio.run(talk_to_playtak())
