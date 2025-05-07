import hashlib
import re


def generate_light_color(user_id):
    # Hash the user_id to get a unique, consistent value
    hash_object = hashlib.sha256(user_id.encode())
    hash_value = hash_object.hexdigest()

    # Use the first 6 characters of the hash value to generate RGB values
    r = int(hash_value[0:2], 16)
    g = int(hash_value[2:4], 16)
    b = int(hash_value[4:6], 16)

    # To make sure it's a light color, adjust the RGB values so they are on the higher end
    r = min(255, max(220, r + 75))
    g = min(255, max(220, g + 75))
    b = min(255, max(220, b + 75))

    # Convert to hex format
    return f'#{r:02x}{g:02x}{b:02x}'


def blankspace_to_underscore(text):
    # replace all special characters by an underscore
    return re.sub(r'[^a-zA-Z0-9]', '_', text)


def html_text_processing(text):
    # replace all special characters by an underscore
    return (text
            .replace('&', '&amp')
            .replace('<', '&lt')
            .replace('>', '&gt')
            .replace('"', '&quot')
            .replace("'", '&apos')
            )
