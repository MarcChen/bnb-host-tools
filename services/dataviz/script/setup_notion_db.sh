#!/bin/bash
set -euo pipefail

# Usage: ./setup_notion_db.sh [parent_page_id]
# If no parent_page_id is supplied, the default is used.
PARENT_PAGE_ID="${1:-19519fda9f9d80bfb700fa81c0417df3}"

# Ensure NOTION_API env variable is set
if [ -z "${NOTION_API:-}" ]; then
    echo "Error: NOTION_API environment variable must be set" >&2
    exit 1
fi

# Create a Notion database with a title property and two date properties: start_date and end_date.
create_db_response=$(curl -s -X POST "https://api.notion.com/v1/databases" \
    -H "Authorization: Bearer ${NOTION_API}" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: 2022-06-28" \
    -d '{
        "parent": { "page_id": "'"${PARENT_PAGE_ID}"'" },
        "title": [
          {
            "type": "text",
            "text": {
              "content": "Blocked Dates Database"
            }
          }
        ],
        "properties": {
            "Name": { "title": {} },
            "Start Date": { "date": {} },
            "End Date": { "date": {} },
            "Insert Date": { "date": {} }
        }
    }')

# Extract the database id from the response.
database_id=$(echo "$create_db_response" | jq -r '.id')

if [ "$database_id" = "null" ]; then
    echo "Failed to create database:" >&2
    echo "$create_db_response" >&2
    exit 1
fi

echo "Created database with ID: $database_id"
script_dir=$(dirname "$0")
echo "$database_id" > "$script_dir/database_id.txt"
