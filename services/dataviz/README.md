# Notion Data Visualization App

This is a Streamlit application that fetches data from a Notion client, stores it locally as a CSV file, and serves a data visualization web app.

## Setup Instructions

1. Clone the repository.
2. Navigate to the `dataviz` directory.
3. Install the required packages:
   ```
   poetry install --without dev --with streamlit_app
   ```
4. Set up your Notion API key and database ID in your environment variables.
5. Run the Streamlit app:
   ```
   streamlit run src/app.py
   ```

## Usage

The app will fetch data from Notion every 60 seconds and display it in a table format. You can modify the fetching interval by changing the `time.sleep(60)` value in `app.py`.