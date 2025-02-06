import re

# The first group (city) is made optional by wrapping it and the comma in a non-capturing group with ?
price_by_night_guest_regex = re.compile(
    r"bec06f\.jpg\]\s*(?:(?P<city>[A-Za-zÀ-ÖØ-öø-ÿ\s]+),\s*)?(?P<country>[A-Za-zÀ-ÖØ-öø-ÿ]+)(?=\r\n)"
)

def test_regex(sample_text):
    """Run the regex on provided sample_text and print the results."""
    match = price_by_night_guest_regex.search(sample_text)
    if match:
        if match.group("city"):
            print("City:", match.group("city"))
        else:
            print("City: Not provided")
        print("Country:", match.group("country"))
    else:
        print("No match found.")

if __name__ == "__main__":
    sample_text_valid = """
\n\r\nGeorgina\r\n\r\n[https://a0.muscache.com/im/pictures/0d520e2d-fe10-4292-a6b5-3616cbae5d94.jpg]Identité vérifiée · 1 commentaire\r\n\r\n[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]Santiago de Querétaro, Mexico\r\n\
    """

    sample_text_country_only = """
\n\r\nGeorgina\r\n\r\n[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]FR\r\n\
    """

    print("Testing with valid sample (city and country):")
    test_regex(sample_text_valid)
    print("\nTesting with country only sample:")
    test_regex(sample_text_country_only)
