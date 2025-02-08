```mermaid
graph LR
  Gmail -->|Extract Emails| Parser -->|Reservation Codes| CSV
  CSV -->|Analyze| Dashboard
  CSV -->|Guest Counts| Calendar
```

