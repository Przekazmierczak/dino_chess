from django.http import JsonResponse
from django.shortcuts import render
from . import pieces

# Create your views here.
def index(request):
    return render(request, "table/index.html", {
        "board": pieces.curr_board
    })

def square(request):
    row = int(request.GET.get("row"))
    column = int(request.GET.get("column"))
    if pieces.curr_board[row][column] is not None:
        curr_square_piece = pieces.curr_board[row][column].piece
        curr_square_player = pieces.curr_board[row][column].player
    else:
        curr_square_piece = None
        curr_square_player = None

    return JsonResponse({
        "piece": curr_square_piece,
        "player": curr_square_player
    })