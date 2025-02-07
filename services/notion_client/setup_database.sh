#!/bin/bash

# Ensure environment variables are set
if [[ -z "$NOTION_DATABASE_ID" || -z "$NOTION_API_KEY" ]]; then
  echo "Error: Both NOTION_DATABASE_ID and NOTION_API_KEY must be set."
  exit 1
fi

echo "Updating Notion database schema for database ID: ${NOTION_DATABASE_ID}"

curl -X PATCH "https://api.notion.com/v1/databases/${NOTION_DATABASE_ID}" \
  -H "Authorization: Bearer ${NOTION_API_KEY}" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
        "title": [
          {
            "text": {
              "content": "Airbnb Bookings"
            }
          }
        ],
        "description": [
          {
            "text": {
              "content": "Stores Airbnb booking information 🏠"
            }
          }
        ],
        "properties": {
          "Date": { "date": {} },
          "Arrival Date": { "date": {} },
          "Departure Date": { "date": {} },
          "Confirmation Code": { "rich_text": {} },
          "Cost per Night": { "number": {} },
          "Number of Nights": { "number": {} },
          "Total Nights Cost": { "number": {} },
          "Cleaning Fee": { "number": {} },
          "Guest Service Fee": { "number": {} },
          "Host Service Fee": { "number": {} },
          "Tourist Tax": { "number": {} },
          "Total Paid by Guest": { "number": {} },
          "Host Payout": { "number": {} },
          "Number of Adults": { "number": {} },
          "Number of Children": { "number": {} },
          "Country": { "select": {} },
          "City": { "select": {} },
          "Subject": { "rich_text": {} },
          "Insert Date": { "rich_text": {} }
        }
      }'
