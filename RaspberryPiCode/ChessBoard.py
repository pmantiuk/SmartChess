# /usr/bin/env python

#####################################################################
# ChessBoard v2.05 is created by John Eriksson - http://arainyday.se
# It's released under the Gnu Public Licence (GPL)
# Have fun!
# The code is edited to be compatible with newest Python 3.12. Enjoy!
#####################################################################

from copy import deepcopy
from pprint import pprint

class ChessBoard:

    # Color values
    WHITE = 0
    BLACK = 1
    NOCOLOR = -1
    
    # Promotion values
    QUEEN = 1
    ROOK = 2
    KNIGHT = 3
    BISHOP = 4

    # Reason values
    INVALID_MOVE = 1
    INVALID_COLOR = 2
    INVALID_FROM_LOCATION = 3
    INVALID_TO_LOCATION = 4
    MUST_SET_PROMOTION = 5
    GAME_IS_OVER = 6
    AMBIGUOUS_MOVE = 7

    # Result values
    NO_RESULT = 0
    WHITE_WIN = 1
    BLACK_WIN = 2
    STALEMATE = 3
    FIFTY_MOVES_RULE = 4
    THREE_REPETITION_RULE = 5

    # Special moves
    NORMAL_MOVE = 0
    EP_MOVE = 1
    EP_CAPTURE_MOVE = 2
    PROMOTION_MOVE = 3
    KING_CASTLE_MOVE = 4
    QUEEN_CASTLE_MOVE = 5

    # Text move output type
    AN = 0      # g4-e3
    SAN = 1     # Bxe3
    LAN = 2     # Bg4xe3

    _game_result = 0 
    _reason = 0
            
    # States
    _turn = WHITE
    _white_king_castle = True
    _white_queen_castle = True
    _black_king_castle = True
    _black_queen_castle = True
    _board = None
    _ep = [0,0]      #none or the location of the current en pessant pawn
    _fifty = 0

    _black_king_location = (0,0)
    _white_king_location = (0,0)    
    
    # three rep stack
    _three_rep_stack = []
    
    # full state stack
    _state_stack = []
    _state_stack_pointer = 0

    # all moves, stored to make it easier to build textmoves
    #[piece,from,to,takes,promotion,check/checkmate,specialmove]
    #["KQRNBP",(fx,fy),(tx,ty),True/False,"QRNB"/None,"+#"/None,0-5]
    _cur_move = [None,None,None,False,None,None,0]
    _moves = []
    
    _promotion_value = 0
    
    def __init__(self):
        self.reset_board()

    def state2str(self):

        b = ""
        for l in self._board:
            b += "%s%s%s%s%s%s%s%s" % (l[0],l[1],l[2],l[3],l[4],l[5],l[6],l[7])
        
        d = (b,
        self._turn,
        self._white_king_castle,
        self._white_queen_castle, 
        self._black_king_castle,
        self._black_queen_castle,
        self._ep[0],
        self._ep[1],
        self._game_result,
        self._fifty)
        
        #turn,wkc,wqc,bkc,bqc,epx,epy,game_result,fifty
        s = "%s%d%d%d%d%d%d%d%d:%d" % d
                            
        return s
            
    def loadCurState(self):
        s = self._state_stack[self._state_stack_pointer-1]
        b= s[:64]
        v = s[64:72]
        f =  int(s[73:])

        idx = 0
        for r in range(8):
            for c in range(8):
                self._board[r][c]=b[idx]
                idx+=1
        
        self._turn                  = int(v[0])
        self._white_king_castle     = int(v[1])
        self._white_queen_castle    = int(v[2]) 
        self._black_king_castle     = int(v[3])
        self._black_queen_castle    = int(v[4])
        self._ep[0]                 = int(v[5])
        self._ep[1]                 = int(v[6])
        self._game_result           = int(v[7])
        
        self._fifty = f
                        
    def pushState(self):
        if self._state_stack_pointer != len(self._state_stack):
            self._state_stack = self._state_stack[:self._state_stack_pointer]
            self._three_rep_stack = self._three_rep_stack[:self._state_stack_pointer]
            self._moves = self._moves[:self._state_stack_pointer-1]

        three_state = [
            self._white_king_castle,
            self._white_queen_castle,
            self._black_king_castle,
            self._black_queen_castle,
            deepcopy(self._board),
            deepcopy(self._ep)
        ]
        self._three_rep_stack.append(three_state)

        state_str = self.state2str()
        self._state_stack.append(state_str)

        self._state_stack_pointer = len(self._state_stack)

    def pushMove(self):
        self._moves.append(deepcopy(self._cur_move))

    def threeRepetitions(self):
        ts = self._three_rep_stack[:self._state_stack_pointer]

        if not len(ts):
            return False

        last = ts[len(ts)-1]
        if ts.count(last) == 3:
            return True
        return False

    def updateKingLocations(self):
        for y in range(0, 8):
            for x in range(0, 8):
                if self._board[y][x] == "K":
                    self._white_king_location = (x, y)
                if self._board[y][x] == "k":
                    self._black_king_location = (x, y)

    def setEP(self, epPos):
        self._ep[0], self._ep[1] = epPos

    def clearEP(self):
        self._ep[0] = 0
        self._ep[1] = 0

    def endGame(self, reason):
        self._game_result = reason

    def checkKingGuard(self, fromPos, moves, specialMoves={}):
        result = []

        if self._turn == self.WHITE:
            kx, ky = self._white_king_location
        else:
            kx, ky = self._black_king_location

        fx, fy = fromPos

        done = False
        fp = self._board[fy][fx]
        self._board[fy][fx] = "."
        if not self.isThreatened(kx, ky):
            done = True
        self._board[fy][fx] = fp

        if done:
            return moves

        for m in moves:
            tx, ty = m
            sp = None
            fp = self._board[fy][fx]
            tp = self._board[ty][tx]

            self._board[fy][fx] = "."
            self._board[ty][tx] = fp

            if specialMoves.get(m) == self.EP_CAPTURE_MOVE:
                sp = self._board[self._ep[1]][self._ep[0]]
                self._board[self._ep[1]][self._ep[0]] = "."

            if not self.isThreatened(kx, ky):
                result.append(m)

            if sp:
                self._board[self._ep[1]][self._ep[0]] = sp

            self._board[fy][fx] = fp
            self._board[ty][tx] = tp

        return result

    def isFree(self, x, y):
        return self._board[y][x] == '.'

    def getColor(self, x, y):
        if self._board[y][x] == '.':
            return self.NOCOLOR
        elif self._board[y][x].isupper():
            return self.WHITE
        elif self._board[y][x].islower():
            return self.BLACK

    def isThreatened(self, lx, ly, player=None):
        
        if player is None:
            player = self._turn

        if player == self.WHITE:
            if 0 < lx < 7 and 0 < ly and self._board[ly-1][lx+1] == 'p':
                 return True
            elif 0 < lx and 0 < ly and self._board[ly-1][lx-1] == 'p':
                return True
        else:
            if 0 < lx < 7 and 0 < ly < 7 and self._board[ly+1][lx+1] == 'P':
                return True
            elif 0 < lx and 0 < ly < 7 and self._board[ly+1][lx-1] == 'P':
                return True

        m = [(lx+1, ly+2), (lx+2, ly+1), (lx+2, ly-1), (lx+1, ly-2), (lx-1, ly+2), (lx-2, ly+1), (lx-1, ly-2), (lx-2, ly-1)]
        for p in m:
            if 0 <= p[0] <= 7 and 0 <= p[1] <= 7:
                if self._board[p[1]][p[0]] == "n" and player == self.WHITE:
                    return True
                elif self._board[p[1]][p[0]] == "N" and player == self.BLACK:
                    return True

        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
        for d in dirs:
            x = lx
            y = ly
            dx, dy = d
            steps = 0
            while True:
                steps += 1
                x += dx
                y += dy
                if x < 0 or x > 7 or y < 0 or y > 7:
                    break
                if self.isFree(x, y):
                    continue
                elif self.getColor(x, y) == player:
                    break
                else:
                    p = self._board[y][x].upper()
                    if p == 'K' and steps == 1:
                        return True
                    elif p == 'Q':
                        return True
                    elif p == 'R' and abs(dx) != abs(dy):
                        return True
                    elif p == 'B' and abs(dx) == abs(dy):
                        return True
                    break
            return False
    
    
        def has_any_valid_moves(self, player=None):
            if player is None:
                player = self._turn

            for y in range(8):
                for x in range(8):
                    if self.get_color(x, y) == player:
                        if len(self.get_valid_moves((x, y))):
                            return True
            return False


# -----------------------------------------------------------------
    def trace_valid_moves(self, from_pos, dirs, max_steps=8):
        moves = []
        for d in dirs:
            x, y = from_pos
            dx, dy = d
            steps = 0
            while True:
                x += dx
                y += dy
                if x < 0 or x > 7 or y < 0 or y > 7:
                    break
                if self.is_free(x, y):
                    moves.append((x, y))
                elif self.get_color(x, y) != self._turn:
                    moves.append((x, y))
                    break
                else:
                    break
                steps += 1
                if steps == max_steps:
                    break
        return moves


    def get_valid_queen_moves(self, from_pos):
        moves = []
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]

        moves = self.trace_valid_moves(from_pos, dirs)

        moves = self.check_king_guard(from_pos, moves)

        return moves


    def get_valid_rook_moves(self, from_pos):
        moves = []
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        moves = self.trace_valid_moves(from_pos, dirs)

        moves = self.check_king_guard(from_pos, moves)

        return moves


    def get_valid_bishop_moves(self, from_pos):
        moves = []
        dirs = [(1, 1), (-1, 1), (1, -1), (-1, -1)]

        moves = self.trace_valid_moves(from_pos, dirs)

        moves = self.check_king_guard(from_pos, moves)

        return moves


    def get_valid_pawn_moves(self, from_pos):
        moves = []
        special_moves = {}
        fx, fy = from_pos

        if self._turn == self.WHITE:
            move_dir = -1
            start_row = 6
            opp_color = self.BLACK
            ep_row = 3
        else:
            move_dir = 1
            start_row = 1
            opp_color = self.WHITE
            ep_row = 4

        if self.is_free(fx, fy + move_dir):
            moves.append((fx, fy + move_dir))

        if fy == start_row:
            if self.is_free(fx, fy + move_dir) and self.is_free(fx, fy + (move_dir * 2)):
                moves.append((fx, fy + (move_dir * 2)))
                special_moves[(fx, fy + (move_dir * 2))] = self.EP_MOVE
        if 0 <= fx < 7 and self.get_color(fx + 1, fy + move_dir) == opp_color:
            moves.append((fx + 1, fy + move_dir))
        if 0 < fx <= 7 and self.get_color(fx - 1, fy + move_dir) == opp_color:
            moves.append((fx - 1, fy + move_dir))

        if fy == ep_row and self._ep[1] != 0:
            if self._ep[0] == fx + 1:
                moves.append((fx + 1, fy + move_dir))
                special_moves[(fx + 1, fy + move_dir)] = self.EP_CAPTURE_MOVE
            if self._ep[0] == fx - 1:
                moves.append((fx - 1, fy + move_dir))
                special_moves[(fx - 1, fy + move_dir)] = self.EP_CAPTURE_MOVE

        moves = self.check_king_guard(from_pos, moves, special_moves)

        return moves, special_moves

    def getValidKnightMoves(self, fromPos):
        moves = []
        fx, fy = fromPos
        m = [(fx + 1, fy + 2), (fx + 2, fy + 1), (fx + 2, fy - 1), (fx + 1, fy - 2),
             (fx - 1, fy + 2), (fx - 2, fy + 1), (fx - 1, fy - 2), (fx - 2, fy - 1)]

        for p in m:
            if 0 <= p[0] <= 7 and 0 <= p[1] <= 7:
                if self.getColor(p[0], p[1]) != self._turn:
                    moves.append(p)

        moves = self.checkKingGuard(fromPos, moves)

        return moves

    def getValidKingMoves(self, fromPos):
        moves = []
        specialMoves = {}

        if self._turn == self.WHITE:
            c_row = 7
            c_king = self._white_king_castle
            c_queen = self._white_queen_castle
            k = "K"
        else:
            c_row = 0
            c_king = self._black_king_castle
            c_queen = self._black_queen_castle
            k = "k"

        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]

        t_moves = self.traceValidMoves(fromPos, dirs, 1)
        moves = []

        self._board[fromPos[1]][fromPos[0]] = '.'

        for m in t_moves:
            if not self.isThreatened(m[0], m[1]):
                moves.append(m)

        if c_king:
            if self.isFree(5, c_row) and self.isFree(6, c_row) and self._board[c_row][7].upper() == 'R':
                if not self.isThreatened(4, c_row) and not self.isThreatened(5, c_row) and not self.isThreatened(6, c_row):
                    moves.append((6, c_row))
                    specialMoves[(6, c_row)] = self.KING_CASTLE_MOVE
        if c_queen:
            if self.isFree(3, c_row) and self.isFree(2, c_row) and self.isFree(1, c_row) and self._board[c_row][0].upper() == 'R':
                if not self.isThreatened(4, c_row) and not self.isThreatened(3, c_row) and not self.isThreatened(2, c_row):
                    moves.append((2, c_row))
                    specialMoves[(2, c_row)] = self.QUEEN_CASTLE_MOVE

        self._board[fromPos[1]][fromPos[0]] = k

        return moves, specialMoves

    def movePawn(self, fromPos, toPos):
        moves, specialMoves = self.getValidPawnMoves(fromPos)

        if toPos not in moves:
            return False

        if toPos in specialMoves:
            t = specialMoves[toPos]
        else:
            t = 0

        if t == self.EP_CAPTURE_MOVE:
            self._board[self._ep[1]][self._ep[0]] = '.'
            self._cur_move[3] = True
            self._cur_move[6] = self.EP_CAPTURE_MOVE

        pv = self._promotion_value
        if self._turn == self.WHITE and toPos[1] == 0:
            if pv == 0:
                self._reason = self.MUST_SET_PROMOTION
                return False
            pc = ['Q', 'R', 'N', 'B']
            p = pc[pv - 1]
            self._cur_move[4] = p
            self._cur_move[6] = self.PROMOTION_MOVE
        elif self._turn == self.BLACK and toPos[1] == 7:
            if pv == 0:
                self._reason = self.MUST_SET_PROMOTION
                return False
            pc = ['q', 'r', 'n', 'b']
            p = pc[pv - 1]
            self._cur_move[4] = p
            self._cur_move[6] = self.PROMOTION_MOVE
        else:
            p = self._board[fromPos[1]][fromPos[0]]

        if t == self.EP_MOVE:
            self.setEP(toPos)
            self._cur_move[6] = self.EP_MOVE
        else:
            self.clearEP()

        if self._board[toPos[1]][toPos[0]] != '.':
            self._cur_move[3] = True

        self._board[toPos[1]][toPos[0]] = p
        self._board[fromPos[1]][fromPos[0]] = "."
        self._fifty = 0

        return True

    def moveKnight(self, fromPos, toPos):
        moves = self.getValidKnightMoves(fromPos)

        if toPos not in moves:
            return False

        self.clearEP()

        if self._board[toPos[1]][toPos[0]] == ".":
            self._fifty += 1
        else:
            self._fifty = 0
            self._cur_move[3] = True

        self._board[toPos[1]][toPos[0]] = self._board[fromPos[1]][fromPos[0]]
        self._board[fromPos[1]][fromPos[0]] = "."
        return True

    def move_king(self, from_pos, to_pos):
        if self._turn == self.WHITE:
            c_row = 7
            k = "K"
            r = "R"
        else:
            c_row = 0
            k = "k"
            r = "r"
        
        moves, special_moves = self.get_valid_king_moves(from_pos)

        if to_pos not in moves:
            return False

        self.clear_EP()

        if self._turn == self.WHITE:
            self._white_king_castle = False
            self._white_queen_castle = False
        else:
            self._black_king_castle = False
            self._black_queen_castle = False

        if special_moves.get(to_pos):
            t = special_moves[to_pos]
        else:
            t = 0

        if t == self.KING_CASTLE_MOVE:
            self._fifty += 1
            self._board[c_row][4] = "."
            self._board[c_row][6] = k
            self._board[c_row][7] = "."
            self._board[c_row][5] = r
            self._cur_move[6] = self.KING_CASTLE_MOVE
        elif t == self.QUEEN_CASTLE_MOVE:
            self._fifty += 1
            self._board[c_row][4] = "."
            self._board[c_row][2] = k
            self._board[c_row][0] = "."
            self._board[c_row][3] = r
            self._cur_move[6] = self.QUEEN_CASTLE_MOVE
        else:
            if self._board[to_pos[1]][to_pos[0]] == ".":
                self._fifty += 1
            else:
                self._fifty = 0
                self._cur_move[3] = True
                
            self._board[to_pos[1]][to_pos[0]] = self._board[from_pos[1]][from_pos[0]]
            self._board[from_pos[1]][from_pos[0]] = "."

            self.update_king_locations()
            return True


    def move_queen(self, from_pos, to_pos):
        moves = self.get_valid_queen_moves(from_pos)

        if to_pos not in moves:
            return False

        self.clear_EP()

        if self._board[to_pos[1]][to_pos[0]] == ".":
            self._fifty += 1
        else:
            self._fifty = 0
            self._cur_move[3] = True

        self._board[to_pos[1]][to_pos[0]] = self._board[from_pos[1]][from_pos[0]]
        self._board[from_pos[1]][from_pos[0]] = "."
        return True


    def move_bishop(self, from_pos, to_pos):
        moves = self.get_valid_bishop_moves(from_pos)

        if to_pos not in moves:
            return False

        self.clear_EP()

        if self._board[to_pos[1]][to_pos[0]] == ".":
            self._fifty += 1
        else:
            self._fifty = 0
            self._cur_move[3] = True

        self._board[to_pos[1]][to_pos[0]] = self._board[from_pos[1]][from_pos[0]]
        self._board[from_pos[1]][from_pos[0]] = "."
        return True


    def move_rook(self, from_pos, to_pos):
        moves = self.get_valid_rook_moves(from_pos)

        if to_pos not in moves:
            return False

        fx, fy = from_pos
        if self._turn == self.WHITE:
            if fx == 0:
                self._white_queen_castle = False
            if fx == 7:
                self._white_king_castle = False
        if self._turn == self.BLACK:
            if fx == 0:
                self._black_queen_castle = False
            if fx == 7:
                self._black_king_castle = False

        self.clear_EP()

        if self._board[to_pos[1]][to_pos[0]] == ".":
            self._fifty += 1
        else:
            self._fifty = 0
            self._cur_move[3] = True

        self._board[to_pos[1]][to_pos[0]] = self._board[from_pos[1]][from_pos[0]]
        self._board[from_pos[1]][from_pos[0]] = "."
        return True

    def _parse_text_move(self, txt):
        txt = txt.strip()
        promotion = None
        dest_x = 0
        dest_y = 0
        h_piece = "P"
        h_rank = -1
        h_file = -1

        # handle the special
        if txt == "O-O":
            if self._turn == 0:
                return (None, 4, 7, 6, 7, None)
            if self._turn == 1:
                return (None, 4, 0, 6, 0, None)
        if txt == "O-O-O":
            if self._turn == 0:
                return (None, 4, 7, 2, 7, None)
            if self._turn == 1:
                return (None, 4, 0, 2, 0, None)

        files = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
        ranks = {"8": 0, "7": 1, "6": 2, "5": 3, "4": 4, "3": 5, "2": 6, "1": 7}

        # Clean up the text move
        "".join(txt.split("e.p."))
        t = []
        for ch in txt:
            if ch not in "KQRNBabcdefgh12345678":
                continue
            t.append(ch)

        if len(t) < 2:
            return None

        # Get promotion if any
        if t[-1] in ('Q', 'R', 'N', 'B'):
            promotion = {'Q': 1, 'R': 2, 'N': 3, 'B': 4}[t.pop()]

        if len(t) < 2:
            return None

        # Get the destination
        if t[-2] not in files or t[-1] not in ranks:
            return None

        dest_x = files[t[-2]]
        dest_y = ranks[t[-1]]

        # Pick out the hints
        t = t[:-2]
        for h in t:
            if h in ('K', 'Q', 'R', 'N', 'B', 'P'):
                h_piece = h
            elif h in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'):
                h_file = files[h]
            elif h in ('1', '2', '3', '4', '5', '6', '7', '8'):
                h_rank = ranks[h]

        # If we have both a source and destination we don't need the piece hint.
        # This will make us make the move directly.
        if h_rank > -1 and h_file > -1:
            h_piece = None

        return (h_piece, h_file, h_rank, dest_x, dest_y, promotion)


    def _format_text_move(self, move, format):
        # piece, from, to, take, promotion, check
        piece = move[0]
        fpos = tuple(move[1])
        tpos = tuple(move[2])
        take = move[3]
        promo = move[4]
        check = move[5]
        special = move[6]

        files = "abcdefgh"
        ranks = "87654321"
        if format == self.AN:
            res = "%s%s%s%s" % (files[fpos[0]], ranks[fpos[1]], files[tpos[0]], ranks[tpos[1]])
        elif format == self.LAN:

            if special == self.KING_CASTLE_MOVE:
                return "O-O"
            elif special == self.QUEEN_CASTLE_MOVE:
                return "O-O-O"

            tc = "-"
            if take:
                tc = "x"
            pt = ""
            if promo:
                pt = "=%s" % promo
            if piece == "P":
                piece = ""
            if not check:
                check = ""
            res = "%s%s%s%s%s%s%s%s" % (piece, files[fpos[0]], ranks[fpos[1]], tc, files[tpos[0]], ranks[tpos[1]], pt, check)
        elif format == self.SAN:

            if special == self.KING_CASTLE_MOVE:
                return "O-O"
            elif special == self.QUEEN_CASTLE_MOVE:
                return "O-O-O"

            tc = ""
            if take:
                tc = "x"
            pt = ""
#----------------------------------------------------------------------------
# PUBLIC METHODS
#----------------------------------------------------------------------------

    def reset_board(self):
        """
        Resets the chess board and all states.
        """
        self._board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['P'] * 8,
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
        self._turn = self.WHITE
        self._white_king_castle = True
        self._white_queen_castle = True
        self._black_king_castle = True
        self._black_queen_castle = True
        self._ep = [0, 0]
        self._fifty = 0
        self._three_rep_stack = []
        self._state_stack = []
        self._moves = []
        self._reason = 0
        self._game_result = 0
        self.push_state()
        self.update_king_locations()


    def set_fen(self, fen):
        """
        Sets the board and states according to a Forsyth-Edwards Notation string.
        Ex. 'rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2'
        """
        self._three_rep_stack = []
        self._state_stack = []
        self._moves = []
        self._reason = 0
        self._game_result = 0

        fparts = fen.split()
        new_state = ""

        # BOARD
        for c in fparts[0]:
            if c in "kqrnbpKQRNBP":
                new_state += c
            elif c in "12345678":
                new_state += '.' * int(c)
        # TURN
        new_state += str("wb".index(fparts[1]))

        # CASTLING
        kq = "KQkq"
        for p in kq:
            if p in fparts[2]:
                new_state += "1"
            else:
                new_state += "0"

        # EN PASSANT
        if len(fparts[3]) == 2:
            new_state += str("abcdefgh".index(fparts[3][0].lower()))
            new_state += str("87654321".index(fparts[3][1]))
        else:
            new_state += "00"

        # GAME RESULT
        new_state += "0"

        # HALF COUNT
        new_state += ":%s" % fparts[4]

        self._state_stack.append(new_state)
        self._state_stack_pointer = 1
        self.load_cur_state()

        three_state = [self._white_king_castle,
                    self._white_queen_castle,
                    self._black_king_castle,
                    self._black_queen_castle,
                    deepcopy(self._board),
                    deepcopy(self._ep)]

        self._three_rep_stack.append(three_state)

        self.update_king_locations()


    def get_fen(self):
        """
        Returns the current state as a Forsyth-Edwards Notation string.
        """
        s = self._state_stack[self._state_stack_pointer - 1]

        b = s[:64]
        v = s[64:72]
        fifty = s[73:]

        rows = []
        for i in range(8):
            row = b[i * 8:(i + 1) * 8]
            cnt = 0
            res = ""
            for c in row:
                if c == ".":
                    cnt += 1
                else:
                    if cnt:
                        res += str(cnt)
                        cnt = 0
                    res += c
            if cnt:
                res += str(cnt)
            rows.append(res)
        board = "/".join(rows)

        turn = (["w", "b"])[int(v[0])]

        kq = ""
        if int(v[1]):
            kq += "K"
        if int(v[2]):
            kq += "Q"
        if int(v[3]):
            kq += "k"
        if int(v[4]):
            kq += "q"
        if not kq:
            kq = "-"

        x = int(v[5])
        y = int(v[6])
        ep = "-"
        if not (x == 0 and y == 0):
            if turn == "b" and (self._board[y][x - 1] == 'p' or self._board[y][x + 1] == 'p'):
                ep = "%s%s" % (("abcdefgh")[x], ("87654321")[y + 1])
            elif turn == "w" and (self._board[y][x - 1] == 'P' or self._board[y][x + 1] == 'P'):
                ep = "%s%s" % (("abcdefgh")[x], ("87654321")[y - 1])

        move = (self._state_stack_pointer + 1) / 2

        return "%s %s %s %s %s %d" % (board, turn, kq, ep, fifty, move)

    def get_move_count(self):
        """
        Returns the number of halfmoves in the stack.
        Zero (0) means no moves have been made.
        """
        return len(self._state_stack) - 1


    def get_current_move(self):
        """
        Returns the current halfmove number. Zero (0) means before the first move.
        """
        return self._state_stack_pointer - 1


    def goto_move(self, move):
        """
        Goto the specified halfmove. Zero (0) is before the first move.
        Return False if the move is out of range.
        """
        move += 1
        if move > len(self._state_stack):
            return False
        if move < 1:
            return False

        self._state_stack_pointer = move
        self.load_cur_state()


    def goto_first(self):
        """
        Goto before the first known move.
        """
        self._state_stack_pointer = 1
        self.load_cur_state()


    def goto_last(self):
        """
        Goto after the last known move.
        """
        self._state_stack_pointer = len(self._state_stack)
        self.load_cur_state()


    def undo(self):
        """
        Undo the last move. Can be used to step back until the initial board setup.
        Returns True or False if no more moves can be undone.
        """
        if self._state_stack_pointer <= 1:
            return False
        self._state_stack_pointer -= 1
        self.load_cur_state()
        return True


    def redo(self):
        """
        If you used the undo method to step backward, you can use this method to step forward until the last move is reached.
        Returns True or False if no more moves can be redone.
        """
        if self._state_stack_pointer == len(self._state_stack):
            return False
        self._state_stack_pointer += 1
        self.load_cur_state()
        return True


    def set_promotion(self, promotion):
        """
        Tell the chessboard how to promote a pawn.
        1=QUEEN, 2=ROOK, 3=KNIGHT, 4=BISHOP
        You can also set promotion to 0 (zero) to reset the promotion value.
        """
        self._promotion_value = promotion


    def get_promotion(self):
        """
        Returns the current promotion value.
        1=QUEEN, 2=ROOK, 3=KNIGHT, 4=BISHOP
        """
        return self._promotion_value


    def is_check(self):
        """
        Returns True if the current player's king is checked.
        """
        if self._turn == self.WHITE:
            kx, ky = self._white_king_location
        else:
            kx, ky = self._black_king_location

        return self.is_threatened(kx, ky, self._turn)


    def is_game_over(self):
        """
        Returns True if the game is over by either checkmate or draw.
        """
        if self._game_result:
            return True
        return False


    def get_game_result(self):
        """
        Returns the reason for game over.
        It can be the following reasons: 1=WHITE_WIN, 2=BLACK_WIN, 3=STALEMATE, 4=FIFTY_MOVES_RULE, 5=THREE_REPETITION_RULE.
        If the game is not over, this method returns zero (0).
        """
        return self._game_result


    def get_board(self):
        """
        Returns a copy of the current board layout. Uppercase letters for white, lowercase for black.
        K=King, Q=Queen, B=Bishop, N=Night, R=Rook, P=Pawn.
        Empty squares are marked with a period (.)
        """
        return deepcopy(self._board)


    def get_turn(self):
        """
        Returns the current player. 0=WHITE, 1=BLACK.
        """
        return self._turn


    def get_reason(self):
        """
        Returns the reason for why addMove returned False.
        1=INVALID_MOVE, 2=INVALID_COLOR, 3=INVALID_FROM_LOCATION, 4=INVALID_TO_LOCATION, 5=MUST_SET_PROMOTION, 6=GAME_IS_OVER
        """
        return self._reason
    
    def get_valid_moves(self, location):
        """
        Returns a list of valid moves. (ex [ [3,4],[3,5],[3,6] ... ] ) If there isn't a valid piece on that location or the piece on the selected
        location hasn't got any valid moves, an empty list is returned.
        The location argument must be a tuple containing an x, y value Ex. (3,3)
        """
        if self._game_result:
            return []

        x, y = location

        if x < 0 or x > 7 or y < 0 or y > 7:
            return False

        self.update_king_locations()

        if self.get_color(x, y) != self._turn:
            return []

        p = self._board[y][x].upper()
        if p == 'P':
            m, s = self.get_valid_pawn_moves(location)
            return m
        elif p == 'R':
            return self.get_valid_rook_moves(location)
        elif p == 'B':
            return self.get_valid_bishop_moves(location)
        elif p == 'Q':
            return self.get_valid_queen_moves(location)
        elif p == 'K':
            m, s = self.get_valid_king_moves(location)
            return m
        elif p == 'N':
            return self.get_valid_knight_moves(location)
        else:
            return []


    def add_move(self, from_pos, to_pos):
        """
        Tries to move the piece located om fromPos to toPos. Returns True if that was a valid move.
        The position arguments must be tuples containing x,y value Ex. (4,6).
        This method also detects game over.

        If this method returns False, you can use the get_reason method to determine why.
        """
        self._reason = 0
        # piece, from, to, take, promotion, check, specialmove
        self._cur_move = [None, None, None, False, None, None, self.NORMAL_MOVE]

        if self._game_result:
            self._result = self.GAME_IS_OVER
            return False

        self.update_king_locations()

        fx, fy = from_pos
        tx, ty = to_pos

        self._cur_move[1] = from_pos
        self._cur_move[2] = to_pos

        # check invalid coordinates
        if fx < 0 or fx > 7 or fy < 0 or fy > 7:
            self._reason = self.INVALID_FROM_LOCATION
            return False

        # check invalid coordinates
        if tx < 0 or tx > 7 or ty < 0 or ty > 7:
            self._reason = self.INVALID_TO_LOCATION
            return False

        # check if any move at all
        if fx == tx and fy == ty:
            self._reason = self.INVALID_TO_LOCATION
            return False

        # check if piece on location
        if self.is_free(fx, fy):
            self._reason = self.INVALID_FROM_LOCATION
            return False

        # check color of piece
        if self.get_color(fx, fy) != self._turn:
            self._reason = self.INVALID_COLOR
            return False

        # Call the correct handler
        p = self._board[fy][fx].upper()
        self._cur_move[0] = p
        if p == 'P':
            if not self.move_pawn((fx, fy), (tx, ty)):
                if not self._reason:
                    self._reason = self.INVALID_MOVE
                return False
        elif p == 'R':
            if not self.move_rook((fx, fy), (tx, ty)):
                self._reason = self.INVALID_MOVE
                return False
        elif p == 'B':
            if not self.move_bishop((fx, fy), (tx, ty)):
                self._reason = self.INVALID_MOVE
                return False
        elif p == 'Q':
            if not self.move_queen((fx, fy), (tx, ty)):
                self._reason = self.INVALID_MOVE
                return False
        elif p == 'K':
            if not self.move_king((fx, fy), (tx, ty)):
                self._reason = self.INVALID_MOVE
                return False
        elif p == 'N':
            if not self.move_knight((fx, fy), (tx, ty)):
                self._reason = self.INVALID_MOVE
                return False
        else:
            return False

        if self._turn == self.WHITE:
            self._turn = self.BLACK
        else:
            self._turn = self.WHITE

        if self.is_check():
            self._cur_move[5] = "+"

        if not self.has_any_valid_moves():
            if self.is_check():
                self._cur_move[5] = "#"
                if self._turn == self.WHITE:
                    self.end_game(self.BLACK_WIN)
                else:
                    self.end_game(self.WHITE_WIN)
            else:
                self.end_game(self.STALEMATE)
        else:
            if self._fifty == 100:
                self.end_game(self.FIFTY_MOVES_RULE)
            elif self.three_repetitions():
                self.end_game(self.THREE_REPETITION_RULE)

        self.push_state()
        self.push_move()

        return True
    
    def get_last_move_type(self):
        """
        Returns a value that indicates if the last move was a "special move".
        Returns -1 if no move has been done.
        Return value can be:
        0=NORMAL_MOVE
        1=EP_MOVE (Pawn is moved two steps and is valid for en passant strike)
        2=EP_CAPTURE_MOVE (A pawn has captured another pawn by using the en passant rule)
        3=PROMOTION_MOVE (A pawn has been promoted. Use get_promotion() to see the promotion piece.)
        4=KING_CASTLE_MOVE (Castling on the king side.)
        5=QUEEN_CASTLE_MOVE (Castling on the queen side.)
        """
        if self._state_stack_pointer <= 1:  # No move has been done at this pointer
            return -1

        self.undo()
        move = self._moves[self._state_stack_pointer - 1]
        res = move[6]
        self.redo()

        return res


    def get_last_move(self):
        """
        Returns a tuple containing two tuples describing the move just made using the internal coordinates.
        In the format ((from_x, from_y), (to_x, to_y))
        Ex. ((4, 6), (4, 4))
        Returns None if no moves have been made.
        """
        if self._state_stack_pointer <= 1:  # No move has been done at this pointer
            return None

        self.undo()
        move = self._moves[self._state_stack_pointer - 1]
        res = (move[1], move[2])
        self.redo()

        return res


    def add_text_move(self, txt):
        """
        Adds a move using several different standards of the Algebraic chess notation.
        AN Examples: 'e2e4' 'f1d1' 'd7-d8' 'g1-f3'
        SAN Examples: 'e4' 'Rfxd1' 'd8=Q' 'Nxf3+'
        LAN Examples: 'Pe2e4' 'Rf1xd1' 'Pd7d8=Q' 'Ng1xf3+'
        """
        res = self._parse_text_move(txt)
        if not res:
            self._reason = self.INVALID_MOVE
            return False
        else:
            piece, fx, fy, tx, ty, promo = res

        if promo:
            self.set_promotion(promo)

        if not piece:
            return self.add_move((fx, fy), (tx, ty))

        if self._turn == self.BLACK:
            piece = piece.lower()

        move_to = None
        move_from = None
        found_move = False
        for y in range(8):
            for x in range(8):
                if self._board[y][x] == piece:
                    if fx > -1 and fx != x:
                        continue
                    if fy > -1 and fy != y:
                        continue
                    vm = self.get_valid_moves((x, y))
                    for m in vm:
                        if m[0] == tx and m[1] == ty:
                            if found_move:
                                self._reason = self.AMBIGUOUS_MOVE
                                return False
                            found_move = True
                            move_from = (x, y)
                            move_to = (tx, ty)

        if found_move:
            return self.add_move(move_from, move_to)

        self._reason = self.INVALID_MOVE
        return False


    def get_all_text_moves(self, format=1):
        """
        Returns a list of all moves done so far in Algebraic chess notation.
        Returns None if no moves have been made.
        """
        if self._state_stack_pointer <= 1:  # No move has been done at this pointer
            return None

        res = []

        point = self._state_stack_pointer

        self.goto_first()
        while True:
            move = self._moves[self._state_stack_pointer - 1]
            res.append(self._format_text_move(move, format))
            if self._state_stack_pointer >= len(self._state_stack) - 1:
                break
            self.redo()

        self._state_stack_pointer = point
        self.load_cur_state()

        return res


    def get_last_text_move(self, format=1):
        """
        Returns the latest move as Algebraic chess notation.
        Returns None if no moves have been made.
        """
        if self._state_stack_pointer <= 1:  # No move has been done at this pointer
            return None

        self.undo()
        move = self._moves[self._state_stack_pointer - 1]
        res = self._format_text_move(move, format)
        self.redo()
        return res


    def print_board(self):
        """
        Print the current board layout.
        """
        print("  +-----------------+")
        rank = 8
        for l in self._board:
            print("%d | %s %s %s %s %s %s %s %s |") % (rank, l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7])
            rank -= 1
        print("  +-----------------+")
        print("    A B C D E F G H")
