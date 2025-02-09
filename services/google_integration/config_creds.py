import argparse
import json
import os


def save_tokens(save_dir):
    token_response = {
        "access_token": os.getenv("GOOGLE_ACCESS_TOKEN"),
        "scope": "https://www.googleapis.com/auth/drive https://mail.google.com/ https://www.googleapis.com/auth/calendar",
        "token_type": "Bearer",
        "expires_in": 3599,
        "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    }

    # Construct the full save path
    save_path = os.path.join(save_dir, "token.json")

    # Ensure the directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Save the tokens to a file
    with open(save_path, "w") as token_file:
        json.dump(token_response, token_file)

    print(f"Tokens have been saved successfully to {save_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Save Google API tokens to a specified directory."
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        required=True,
        help="The directory to save the token.json file.",
    )

    args = parser.parse_args()

    save_tokens(args.save_dir)
