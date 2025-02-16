# 🏠 BNB Booking Tools: Gmail & Calendar Automation  
*Sync Airbnb guest data, automate cleaning calendars, and track repeat customers.*  

<p align="center">
  <img src="./demo.gif" alt="Project Demo GIF" width="600">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)  

---

## 📖 Overview  
A lightweight tool for Airbnb hosts that:  
✅ **Securely shares booking dates/guest counts** via Google Calendar *(no viewer login required)*  
✅ **Extracts reservation codes** from Gmail to identify returning guests  
✅ Generates **data visualizations** for guest demographics and booking trends  

---

## ✨ Features  
- **Public-Facing Calendar**: Auto-updates with guest counts for cleaning staff (no Google account needed to view).  
- **Gmail Scraper**: Parses Airbnb emails to collect reservation codes, nationalities, and stay dates.  
- **Discount Management**: Flags repeat guests for custom pricing rules.  
- **Analytics Dashboard**: Visualizes booking patterns and guest origins.

---

## 🚀 Use Cases  
- **🧹 Cleaning Staff Coordination**:  
  Provide cleaning staff with easy access to the number of guests for each booking without exposing sensitive booking details.
  
- **🔄 Repeat Customer Tracking**:  
  Identify returning guests using reservation codes and apply discounts or special offers.
  
- **📊 Guest Insights**:  
  Analyze guest data to understand booking patterns, popular travel seasons, and geographical preferences.

---

## 🛠️ Technologies Used  
- **Google APIs**:  
  - **Gmail API**: For extracting booking-related emails.  
  - **Calendar API**: For creating and managing custom calendars.
  
- **Data Storage**:  
  - Notion Database for storing extracted data.
  
- **Data Visualization**:  
  - To Be Determined ...
  
- **Authentication**:  
  - OAuth2 for secure access to Google APIs.
