# Interactive Chessboard - www.DIYmachines.co.uk
# This codes includes large sections kindly shared on www.chess.fortherapy.co.uk, which itself incorporates alot of other peoples code.
# Please feel free to modify, adapt and share. Any excisting licenses included must remain intact as well as including acknowledgment to those who have contribued.
# This program plays chess using Stockfish the open source chess engine, using the ChessBoard library to manage the board.
# It is written in Python 2.7 because chessboard is.
# It assumes you have got the python libraries chessboard, subprocess and time

import subprocess
import time
import serial
from ChessBoard import ChessBoard

maxchess = ChessBoard()

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)   # for Pi Zero use '/dev/ttyAMA0' and for others use '/dev/ttyUSB0'.
    ser.flush()

# initiate stockfish chess engine

engine = subprocess.Popen(
    'stockfish',
    universal_newlines=True,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE
    )

def get():
    stx=""
    engine.stdin.write('isready\n')
    print('\nengine:')
    while True:
        text = engine.stdout.readline().strip()
        if text == 'readyok':
            break
        if text !='':
            print('\t'+text)
        if text[0:8] == 'bestmove':
            return text

def putAdafruit(command):
    print('\nTrying to send to AdafruitIO:\n\t'+command)
    remotePlayer.stdin.write("send\n")
    remotePlayer.stdin.write(colourChoice+'\n')
    remotePlayer.stdin.write(command+'\n')
    while True:
        text = remotePlayer.stdout.readline().strip()
        if text[6:17] == 'piece moved':
            print(text)
            break

def getAdafruit():
    print('\nTrying to read remote boards move from AdafruitIO:\n\t')
    remotePlayer.stdin.write("receive\n")
    remotePlayer.stdin.write(colourChoice+'\n')
    while True:
        text = remotePlayer.stdout.readline().strip()
        print('The remote move was: ' + text)
        return text

def sget():
    stx=""
    engine.stdin.write('isready\n')
    print('\nengine:')
    while True:
        text = engine.stdout.readline().strip()
        if text !='':
            print('\t'+text)
        if text[0:8] == 'bestmove':
            mtext=text
            return mtext

def getboard():
    print("\n Waiting for command from the Board")
    while True:
        if ser.in_waiting > 0:
            btxt = ser.readline().decode('utf-8').rstrip().lower()
            if btxt.startswith('heypixshutdown'):
                shutdownPi()
                break
            if btxt.startswith('heypi'):
                btxt = btxt[len('heypi'):]
                print(btxt)
                return btxt
                break
            else:
                continue

def sendtoboard(stxt):
    print("\n Sent to board: heyArduino" + stxt)
    stxt = bytes(str(stxt).encode('utf8'))
    time.sleep(2)
    ser.write(b"heyArduino" + stxt + "\n".encode('ascii'))

def newgame():
    sendToScreen ('NEW','GAME','','30')
    get()
    put('uci')
    get()
    put('setoption name Skill Level value ' + skill)
    get()
    put('setoption name Hash value 128')
    get()
    put('ucinewgame')
    maxchess.resetBoard()
    maxchess.setPromotion(maxchess.QUEEN)
    print("Promotion set to ")
    print(maxchess.getPromotion())
    fmove=""
    brdmove=""
    time.sleep(2)
    sendToScreen ('Please enter','your move:','')
    return fmove

def newgameOnline():
    maxchess.resetBoard()
    maxchess.setPromotion(maxchess.QUEEN)
    print("Promotion set to ")
    print(maxchess.getPromotion())
    fmove=""
    brdmove=""
    return fmove

def bmove(fmove):
    fmove=fmove
    brdmove = bmessage[1:5].lower()
    if maxchess.addTextMove(brdmove) == False:
        etxt = "error"+ str(maxchess.getReason())+brdmove
        maxchess.printBoard()
        sendToScreen ('Illegal move!','Enter new','move...','14')
        sendtoboard(etxt)
        return fmove
    else:
        maxchess.printBoard()
        print ("brdmove")
        print(brdmove)
        sendToScreen (brdmove[0:2] + '->' + brdmove[2:4] ,'','Thinking...','20')
        fmove = fmove+" " +brdmove
        cmove = "position startpos moves"+fmove
        print (cmove)
        put(cmove)
        put("go movetime " + movetime)
        text = sget()
        print (text)
        smove = text[9:13]
        hint = text[21:25]
        if maxchess.addTextMove(smove) != True:
            stxt = "e"+ str(maxchess.getReason())+smove
            maxchess.printBoard()
            sendtoboard(stxt)
        else:
            temp=fmove
            fmove =temp+" " +smove
            stx = smove+hint
            maxchess.printBoard()
            print ("computer move: " +smove)
            sendToScreen (smove[0:2] + '->' + smove[2:4] ,'','Your go...','20')
            smove ="m"+smove
            sendtoboard(smove +"-"+ hint)
            return fmove

def bmoveOnline(fmove):
    fmove=fmove
    print ("F move is now set to ")
    print(fmove)
    brdmove = bmessage[1:5].lower()
    print ("Brdmove is now set to ")
    print(brdmove)
    if maxchess.addTextMove(brdmove) == False:
        print("The move is illegal")
        etxt = "error"+ str(maxchess.getReason())+brdmove
        maxchess.printBoard()
        sendtoboard(etxt)
        return fmove
    else:
        print("The move is legal")
        maxchess.printBoard()
        print ("brdmove")
        print(brdmove)
        putAdafruit(brdmove)
        fmove = fmove+" " +brdmove
        cmove = "position startpos moves"+fmove
        print (cmove)
        sendToScreen ('Waiting for' ,'the other','Player...','20')
        text = getAdafruit()
        print (text)
        smove = text
        hint = "xxxx"
        temp=fmove
        fmove =temp+" " +smove
        stx = smove+hint
        maxchess.printBoard()
        print ("Remote players move: " +smove)
        if maxchess.addTextMove(smove) != True:
            stxt = "e"+ str(maxchess.getReason())+smove
            maxchess.printBoard()
            sendtoboard(stxt)
        else:
            temp=fmove
            fmove =temp+" " +smove
            stx = smove+hint
            maxchess.printBoard()
            sendToScreen (smove[0:2] + '->' + smove[2:4] ,'','Your go...','20')
            smove ="m"+smove
            sendtoboard(smove +"-"+ hint)
        return fmove

def put(command):
    print('\nyou:\n\t'+command)
    engine.stdin.write(command+'\n')

def shutdownPi():
    sendToScreen ('Shutting down...','Wait 20s then','disconnect power.')
    time.sleep(5)
    from subprocess import call
    call("sudo nohup shutdown -h now", shell=True)
    time.sleep(10)

def sendToScreen(line1,line2,line3,size='14'):
    screenScriptToRun = ["python3", "/home/pi/SmartChess/RaspberryPiCode/printToOLED.py", '-a '+ line1, '-b '+ line2, '-c '+ line3, '-s '+ size]
    subprocess.Popen(screenScriptToRun)

# Choose a mode of gameplay on the Arduino
time.sleep(1)
sendtoboard("ChooseMode")
print ("Waiting for mode of play to be decided on the Arduino")
sendToScreen ('Choose opponent:','1) Against PC','2) Remote human')
gameplayMode = getboard()[1:].lower()
print ("Requested gameplay mode:")
print(gameplayMode)

if gameplayMode == 'stockfish':
    while True:
        sendtoboard("ReadyStockfish")
        print ("Waiting for level command to be received from Arduino")
        sendToScreen ('Choose computer','difficulty level:','(0 -> 8)')
        skillFromArduino = getboard()[1:3].lower()
        print ("Requested skill level:")
        print(skillFromArduino)
        print ("Waiting for move time command to be received from Arduino")
        sendToScreen ('Choose computer','move time:','(0 -> 8)')
        movetimeFromArduino = getboard()[1:].lower()
        print ("Requested time out setting:")
        print(movetimeFromArduino)
        print ("\n Chess Program \n")
        sendToScreen ('NEW','GAME','','30')
        time.sleep(2)
        sendToScreen ('Please enter','your move:','')
        skill = skillFromArduino
        movetime = movetimeFromArduino
        fmove = newgame()
        while True:
            bmessage = getboard()
            print ("Move command received from Arduino")
            print(bmessage)
            code = bmessage[0]
            fmove=fmove
            if code == 'm':
                print("Fmove is currently: ")
                print(fmove)
                fmove = bmove(fmove)
            elif code == 'n':
                fmove = newgame()
            else:
                sendtoboard('error at option')

elif gameplayMode == 'onlinehuman':
    print("Playing online chosen")
    updateScriptToRun = ["python3", "/home/pi/SmartChess/RaspberryPiCode/update-online.py"]
    remotePlayer = subprocess.Popen(updateScriptToRun,
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    while True:
        time.sleep(1)
        sendtoboard("ReadyOnlinePlay")
        sendToScreen ('Select a colour:','1 = White/First','2 = Black/Second')
        print ("Waiting for colour choice to be received from Arduino")
        colourChoice = getboard()
        print ("Colour choice received from Arduino")
        print(colourChoice)
        if colourChoice == "cblack":
            skipFirstGo = "Yes"
        elif colourChoice == "cwhite":
            skipFirstGo = "No"
        putAdafruit("ready")
        print ("\n Chess Program \n")
        fmove = newgameOnline()
        while True:
            if skipFirstGo == "Yes":
                text = getAdafruit()
                print (text)
                smove = text
                hint = "xxxx"
                temp=fmove
                fmove =temp+" " +smove
                stx = smove+hint
                maxchess.printBoard()
                print ("Remote players move: " +smove)
                if maxchess.addTextMove(smove) != True:
                        stxt = "e"+ str(maxchess.getReason())+smove
                        maxchess.printBoard()
                        sendtoboard(stxt)
                else:
                        temp=fmove
                        fmove =temp+" " +smove
                        stx = smove+hint
                        maxchess.printBoard()
                        sendToScreen (smove[0:2] + '->' + smove[2:4] ,'','Your go...','20')
                        smove ="m"+smove
                        sendtoboard(smove +"-"+ hint)
                        skipFirstGo = "NoMore"
            bmessage = getboard()
            print ("Command received from Arduino")
            print(bmessage)
            code = bmessage[0]
            fmove=fmove
            if code == 'm':
                print("Fmove is currently: ")
                print(fmove)
                fmove = bmoveOnline(fmove)
            elif code == 'n':
                fmove = newgameOnline()
            else:
                sendtoboard('error at option')

