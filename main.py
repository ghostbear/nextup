#!/usr/bin/env python3

from datetime import datetime

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from numpy.core import long
from rich.console import Console

console = Console()

query = gql('''
query getCurrentSeason($page: Int, $season: MediaSeason, $seasonYear: Int, $onList: Boolean) {
  Page(page: $page, perPage: 50) {
    media(season: $season, seasonYear: $seasonYear, onList: $onList) {
      id
      title {
        userPreferred
      }
      episodes
      nextAiringEpisode {
        airingAt
        episode
      }
    }
  }
}
''')


def epochtodate(epoch) -> str:
    return datetime.fromtimestamp(long(epoch)).strftime('%a (%d/%m) at %I:%M %p')


def readtokenfromfile():

    access_token = ""

    with open('setting.txt', 'r') as file:
        try:
            access_token = file.readline()
        except:
            print()

    return access_token


def writetokentofile(access_token):
    with open('setting.txt', 'a') as file:
        file.write(access_token)


def askfortoken() -> str:
    access_token = readtokenfromfile()
    if access_token:
        return access_token

    id = 3721
    url = "https://anilist.co/api/v2/oauth/authorize?client_id=" + str(id) + "&response_type=token"

    console.print("Welcome to [bold blue]NextUp[/bold blue]!")
    console.print("To get started you need to authorize the program")
    console.print("You can do so by heading over to " + url)
    console.print("After you have authorized the program copy & paste the token")
    access_token = console.input("Paste token right here: ")

    if len(access_token) > 100:
        writetokentofile(access_token)
    else:
        print("That is not a token :^/")
        return askfortoken()

    return access_token


def createtransport(access_token: str) -> RequestsHTTPTransport:
    return RequestsHTTPTransport(
        url='https://graphql.anilist.co',
        verify=False,
        retries=3,
        headers={
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    )


def setupclient(transport: RequestsHTTPTransport) -> Client:
    return Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )


def season(month: int):
    month = month + 1

    if month in [12, 1, 2]:
        return "WINTER"

    if month in [3, 4, 5]:
        return "SPRING"

    if month in [6, 7, 8]:
        return "SUMMER"

    if month in [9, 10, 11]:
        return "FALL"


def getcurrentseason(client: Client) -> dict:
    today = datetime.today()
    params = {
        "page": 1,
        "season": season(today.month),
        "seasonYear": today.year,
        "onList": True
    }

    return client.execute(query, variable_values=params)


def printresult(current_season: dict):
    media = list(
        map(
            lambda item: {
                'title': item['title']['userPreferred'],
                'airingAt': item['nextAiringEpisode']['airingAt'],
                'episode': item['nextAiringEpisode']['episode'] if item['nextAiringEpisode']['episode'] else "?",
                'episodes': item['episodes'] if item['episodes'] else "?",
            }, current_season['Page']['media']
        )
    )

    console.print("Here is your [bold blue]NextUp[/bold blue] schedule!")

    for item in sorted(media, key=lambda item: item['airingAt']):
        console.print("[bold blue]{}[/bold blue] episode {} of {} will air on {} ".format(item['title'],
                                                                                item['episode'],
                                                                                item['episodes'],
                                                                                epochtodate(item['airingAt'])))


def main():
    access_token = askfortoken()
    transport = createtransport(access_token)
    client = setupclient(transport)
    current_season = getcurrentseason(client)
    printresult(current_season)


if __name__ == "__main__":
    main()
