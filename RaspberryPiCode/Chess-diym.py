import serial

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.flush()

def getboardMessage():
    """Gets a text string from the board.

    Waits for the startup command from the Board and returns the received text string.
    """
    print("\nWaiting for startup command from the Board")
    while True:
        if ser.in_waiting > 0:
            btxt = ser.readline().decode('utf-8').rstrip().lower()
            if btxt.startswith('heypi'):
                btxt = btxt[len('heypi'):]
                print(btxt)
                return btxt
            else:
                continue

if __name__ == '__main__':
    initialMessage = getboardMessage()

    print("Initial command received from Arduino")
    print(initialMessage)

    import StartChessGame
