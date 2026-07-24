from app.models.move import MoveRecord
from app.utils.formatting import format_move

def test_formats_ordinary_move():
    move = MoveRecord(number=1,
                      colour='white', 
                      piece='white_pawn', 
                      from_square='e2', 
                      to_square='e4', 
                      captured_piece=None)
    assert format_move(move) == "1. White: pawn e2 → e4"

def test_formats_capture():
    move = MoveRecord(number=2,
                      colour='black', 
                      piece='black_pawn', 
                      from_square='d5', 
                      to_square='e4', 
                      captured_piece="white_pawn")
    assert format_move(move) == "2. Black: pawn d5 × e4 (captured white pawn)"