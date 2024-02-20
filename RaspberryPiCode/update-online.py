import time
from Adafruit_IO import Client, Feed, RequestError

# Set to your Adafruit IO key.
# Remember, your key is a secret,
# so make sure not to publish it when you publish this code!
ADAFRUIT_IO_KEY = 'AddYourKeyHere'

# Set to your Adafruit IO username.
# (go to https://accounts.adafruit.com to find your username)
ADAFRUIT_IO_USERNAME = 'AddYourUserNameHere'

# Create an instance of the REST client.
aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

try:  # if we have a 'whiteplayer' feed
    whiteplayermove = aio.feeds('whiteplayermove')
except RequestError:  # create a text-test feed
    feed = Feed(name="whiteplayermove")
    whiteplayermove = aio.create_feed(feed)

try:  # if we have a 'boardb' feed
    blackplayermove = aio.feeds('blackplayermove')
except RequestError:  # create a digital feed
    feed = Feed(name="blackplayermove")
    blackplayermove = aio.create_feed(feed)  # Fix typo: whiteplayermove to blackplayermove

# ----------------------
send_or_receive = "neither"  # Fix variable naming: sendOrReceive to send_or_receive
previous_data = "ready"  # Fix variable naming: previousData to previous_data
colour_choice = "neither"

while True:
    try:
        send_or_receive = input()  # Fix variable naming: sendOrReceive to send_or_receive
    except EOFError:
        continue
    if send_or_receive == "send":  # Fix variable naming: sendOrReceive to send_or_receive
        colour_choice = input()
        if colour_choice == "cwhite":
            chess_piece_moved = input()
            print('White piece moved -> ', chess_piece_moved, ' successfully.')  # Fix variable naming
            aio.send(whiteplayermove.key, chess_piece_moved)
        elif colour_choice == "cblack":
            chess_piece_moved = input()
            print('Black piece moved -> ', chess_piece_moved, ' successfully.')  # Fix variable naming
            aio.send(blackplayermove.key, chess_piece_moved)
    elif send_or_receive == "receive":  # Fix variable naming: sendOrReceive to send_or_receive
        while True:
            if colour_choice == "cwhite":
                data = aio.receive(blackplayermove.key)
                data = data.value.strip().lower()
            elif colour_choice == "cblack":
                data = aio.receive(whiteplayermove.key)
                data = data.value.strip().lower()
            if previous_data != data:
                previous_data = data
                print(data + '\n')
                break
            time.sleep(3)

    # avoid timeout from adafruit io
    time.sleep(2)

