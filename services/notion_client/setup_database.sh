#!/bin/bash

# Ensure environment variables are set
if [[ -z "$DATABASE_ID" || -z "$NOTION_API" ]]; then
  echo "Error: Both DATABASE_ID and NOTION_API must be set."
  exit 1
fi

echo "Updating Notion database schema for database ID: ${DATABASE_ID}"

curl -X PATCH "https://api.notion.com/v1/databases/${DATABASE_ID}" \
  -H "Authorization: Bearer ${NOTION_API}" \
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
          "Arrival Date": { "date": {} },
          "Departure Date": { "date": {} },
          "Confirmation Code": { "rich_text": {} },
          "Price by night": { "number": {} },
          "Number of Nights": { "number": {} },
          "Total Nights Cost": { "number": {} },
          "Cleaning Fee": { "number": {} },
          "Guest Service Fee": { "number": {} },
          "Host Service Fee": { "number": {} },
          "Tourist Tax": { "number": {} },
          "Host Payout": { "number": {} },
          "Number of Adults": { "number": {} },
          "Number of Children": { "number": {} },
          "Country": { "select": {} },
          "City": { "select": {} },
          "Insert Date": { "rich_text": {} },
          "Arrival DayOfWeek": { "rich_text": {} },
          "Departure DayOfWeek": { "rich_text": {} },
          "Host Service Tax": { "rich_text": {} },
          "Price by night": { "number": {} },
          "Guest Payout": { "number": {} },
          "Mail Date": { "date": {} },
          "Rating": { "number": {} },
          "Name": { "title": {} }
        }
      }'
