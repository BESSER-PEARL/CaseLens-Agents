import json
from typing import Generator


def iterate_json_file(filepath: str) -> Generator[dict, None, None]:
    """
    Opens a JSON file containing a list of dictionaries and yields each dictionary.

    :param filepath: Path to the JSON file.
    :yield: Each dictionary in the list.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON file does not contain a list at the top level.")
            for entry in data:
                if isinstance(entry, dict):
                    yield entry
                else:
                    raise ValueError("Encountered non-dictionary item in the list.")
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except json.JSONDecodeError:
        print(f"Could not decode JSON in file: {filepath}")


def update_entry_by_id(filepath: str, entry_id: int, updated_fields: dict) -> bool:
    """
    Updates a dictionary in a JSON file's top-level list by matching its 'id'.

    :param filepath: Path to the JSON file.
    :param entry_id: The ID of the dictionary to update.
    :param updated_fields: A dictionary of fields to update.
    :return: True if the entry was found and updated, False otherwise.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON file does not contain a list at the top level.")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error reading file: {filepath}")
        return False

    # Find and update the matching entry
    updated = False
    for i, item in enumerate(data):
        if isinstance(item, dict) and item.get("id") == entry_id:
            data[i].update(updated_fields)
            updated = True
            break

    if updated:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


def update_json_file(filepath: str, new_entries: list[dict]) -> None:
    """
    Update a JSON file that contains a list of dictionaries by appending new entries.

    :param filepath: Path to the JSON file.
    :param new_entries: List of dictionaries to append to the file.
    """
    try:
        # Read existing data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON file does not contain a list at the top level.")
    except FileNotFoundError:
        # If the file does not exist, initialize with an empty list
        data = []
    except json.JSONDecodeError:
        # If the file is empty or corrupted, also initialize with an empty list
        data = []

    # Append new entries
    data.extend(new_entries)

    # Write updated data back to the file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remove_entries_by_attribute(file_path: str, attribute_name: str, attribute_value: str) -> None:
    """
    Removes all entries from a JSON file (containing a list of dicts)
    where a particular attribute has a specified value.

    Args:
        file_path (str): Path to the JSON file.
        attribute_name (str): The name of the attribute to match in the json entries
        attribute_value (str): The value of the attribute.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON file must contain a top-level list.")

        filtered_data = [entry for entry in data if entry.get(attribute_name) != attribute_value]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON format in file: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
