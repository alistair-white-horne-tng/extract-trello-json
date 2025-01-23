import argparse
import pytz
from dotenv import load_dotenv
import os
from trello import TrelloClient, Card
from datetime import datetime


def get_all_cards() -> list[Card]:
    load_dotenv()

    client = TrelloClient(
        api_key=os.getenv('TRELLO_API_KEY'),
        api_secret=os.getenv('TRELLO_API_SECRET'),
        token=os.getenv('TRELLO_TOKEN')
    )

    board = client.get_board(board_id=os.getenv('TRELLO_BOARD_ID'))

    return board.get_cards()

def extract_cards_since(cards: list[Card], start_date: datetime) -> list[Card]:
    return [
        card for card in cards
        if card.created_date > start_date
    ]

def get_links_from_cards(cards: list[Card]) -> list[str]:
    return [card.url for card in cards]

def extract_cards_with_labels(cards: list[Card], labels: list[str], match_function=all) -> list[Card]:
    # Returns cards whose labels match the `labels` parameter.
    # use match_function = all or any to decide whether to and- or or-match

    lower_labels = [label.lower() for label in labels]

    matched_cards = []

    for card in cards:
        lower_card_labels = [label.name.lower() for label in card.labels]

        if match_function([
            match_label in lower_card_labels for match_label in lower_labels
        ]):
            matched_cards.append(card)

    return matched_cards

def extract_cards_without_labels(cards: list[Card], labels: list[str], match_function=all) -> list[Card]:
    # Returns cards whose labels do NOT match the `labels` parameter.
    # use match_function = all or any to decide whether to and- or or-match

    return extract_cards_with_labels(cards, labels, match_function=lambda booleans: not match_function(booleans))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract cards from Trello board described in .env"
    )
    # parser.add_argument("input", help="Path to the Trello board JSON file")
    # parser.add_argument("output", help="Path where the output CSV should be saved")

    args = parser.parse_args()

    cards = get_all_cards()

    recent_cards = extract_cards_since(cards, datetime(2025, 1, 23, tzinfo=pytz.UTC))

    ops_cards = extract_cards_without_labels(recent_cards, ['ops', 'design'], any)

    print(get_links_from_cards(ops_cards))
