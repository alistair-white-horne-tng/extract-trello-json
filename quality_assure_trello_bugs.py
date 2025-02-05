import argparse
import requests
from dotenv import load_dotenv
import os
from trello import TrelloClient, Card
from datetime import datetime

load_dotenv()


class CustomFieldItem:
    id: str
    value: None
    idValue: str
    idCustomField: str
    idModel: str
    modelType: str



def get_all_cards() -> list[Card]:
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

def extract_archived_cards(cards: list[Card], is_archived: bool=False) -> list[Card]:
    return [card for card in cards if card.closed == is_archived]

def make_api_request(url_extension: str, params: dict={}) -> any:
    url = f"https://api.trello.com/1/{url_extension}"
    authorised_params = params | {
        "key": os.getenv('TRELLO_API_KEY'),
        "token": os.getenv('TRELLO_TOKEN')
    }
    response = requests.get(url, params=authorised_params)
    response.raise_for_status()

    return response.json()

def get_custom_fields(card: Card) -> list[dict[str, str]]:
    data = make_api_request(
        url_extension=f"cards/{card.id}",
        params={
            "fields": "name",
            "customFieldItems": "true",
        }
    )

    custom_fields = []
    for item in data.get("customFieldItems"):
        options = ALL_CUSTOM_FIELDS.get(item.get("idCustomField"))

        custom_fields.append({
            options.get("name", "Not found"): options.get("options", {}).get(item.get("idValue"), "Not found")
        })

    return custom_fields


def get_custom_field_options_map(custom_field) -> dict[str, str]:
    data = make_api_request(url_extension=f"customFields/{custom_field.get("idCustomField")}/options")

    return {option.get("_id"): option.get("value").get("text") for option in data}

def get_all_custom_fields():
    data = make_api_request(url_extension=f"boards/{os.getenv('TRELLO_BOARD_ID')}/customFields")

    return {
        field.get("id") : {
            "name": field.get("name"),
            "options": {
                option.get("id") : option.get("value").get("text")
                for option in field.get("options", [])
            }
        } for field in data
    }


def quality_check(cards: list[Card]):
    defective_cards = {}

    # All bug cards should have a severity
    for card in extract_cards_with_labels(cards, ["bug"]):
        custom_fields = get_custom_fields(card)

        if not "Severity" in custom_fields.keys():
            defective_cards["Bug card has no severity"] = card

    return defective_cards


ALL_CUSTOM_FIELDS = get_all_custom_fields()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract cards from Trello board described in .env"
    )
    # parser.add_argument("input", help="Path to the Trello board JSON file")
    # parser.add_argument("output", help="Path where the output CSV should be saved")

    args = parser.parse_args()

    all_cards = get_all_cards()
    all_cards = extract_archived_cards(all_cards)

    links = get_links_from_cards(all_cards)

    defective_cards = quality_check(all_cards)

    pass
