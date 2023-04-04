from bs4 import BeautifulSoup
import websockets
import asyncio
import json
import os

outcome = {
    'playing': 0,
    'win1': 1,
    'win2': 2,
    'tie': 3,
    'double_lose': 10,
}

category = {
    'Junior': 0,
    'Senior': 1,
    'Master': 2
}


async def main(websocket, path):
    global my_file
    outcomes = {
        '0': 'playing',
        '1': '1',
        '2': '2',
        '3': 'tie',
        '10': 'double_lose',
        'None': 'None'}

    categories = {
        '0': 'Junior',
        '1': 'Senior',
        '2': 'Master',
        '8': 'JR/SR',
        '9': 'SR/MA',
        '10': 'Mixed',
        'None': 'None'}

    print(f"A client just connected {websocket.remote_address[0]}")
    previous_stmtime = 0
    while True:
        current_stmtime = os.stat(my_file).st_mtime
        if current_stmtime != previous_stmtime:
            print('file updated')
            previous_stmtime = current_stmtime

            my_json = {}
            with open(my_file, 'r', encoding='utf-8') as file:
                data = file.read()

            soup = BeautifulSoup(data, 'xml')

            players = soup.find("players").find_all('player')

            my_json['players'] = {}
            for player in players:
                my_json['players'][player['userid']] = f'{player.find("firstname").string} {player.find("lastname").string}'

            pods = soup.find("pods").find_all('pod')

            my_json['round'] = {}
            for pod in pods:
                if pod['category'] not in categories:
                    division = 'None'
                else:
                    division = categories[pod['category']]

                rounds = pod.find('rounds').find_all('round')
                for my_round in rounds:
                    round_number = my_round['number']
                    if round_number not in my_json['round']:
                        my_json['round'][round_number] = {}
                    placeholder = {'table': {}}
                    matches = my_round.find('matches').find_all('match')
                    for match in matches:
                        table_number = match.tablenumber.string
                        player1_id = match.player1['userid']
                        player2_id = match.player2['userid']
                        outcome = match['outcome']
                        if outcome not in outcomes:
                            outcome = 'None'
                        placeholder['table'][table_number] = {'player1': my_json['players'][player1_id],
                                                              'player2': my_json['players'][player2_id],
                                                              'outcome': outcomes[outcome]}

                    my_json['round'][round_number][division] = placeholder

            try:
                data = json.dumps(my_json, indent=4)
                await websocket.send(data)
            except websockets.exceptions.ConnectionClosed as e:
                print("A client just disconnected")

        await asyncio.sleep(1)

my_file = input(r'enter TOM file path (example: C:\Users\Username\TOM_DATA\MyTournament.tdf):')

start_server = websockets.serve(main, "", 7489)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
