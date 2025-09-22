## [0.1.0] - 2025-02-09
- Merged PR #1 by @MarcChen: Feature : Added basic feature of the service 
This pull request includes several significant changes to the project, focusing on configuration updates, workflow automation, and the addition of new services for Google Calendar and Gmail integration.

### Configuration Updates:
* [`.flake8`](diffhunk://#diff-6951dbb399883798a226c1fb496fdb4183b1ab48865e75eddecf6ceb6cf46442R1-R11): Added configuration settings for Flake8, including maximum line length, ignored errors, and directories to exclude.
* [`pyproject.toml`](diffhunk://#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R1-R33): Added project metadata and dependencies using Poetry, including both runtime and development dependencies.

### Workflow Automation:
* [`.github/workflows/run.yml`](diffhunk://#diff-a3ddd7238fc6e36daeb0ef76e93fe15cc87824bd3299888075210c5ca6a474d3R1-R108): Added a new GitHub Actions workflow to automate tasks such as checking out the repository, ensuring Python 3.10 and Poetry are installed, validating dependencies, and running the main script to sync Notion with Google Tasks.

### New Services:
* [`services/google_integration/calendar_services.py`](diffhunk://#diff-c7f9db28c79275a0e196974bd022be6e4429bb6f5559ff021e643c0425d9df51R1-R199): Implemented a `CalendarService` class to manage Google Calendar events, including creating, retrieving, deleting events, and checking for existing events based on reservation codes.
* [`services/google_integration/gmail_services.py`](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46R1-R244): Added a `GmailService` class to handle Gmail API operations, such as tagging emails, marking them as read, listing unread emails, and processing reservation confirmations.

### Main Script:
* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1R1-R5): Added a script to initialize and run the `MailProcessorService`.

### Miscellaneous:
* [`services/mail_processing/__init__.py`](diffhunk://#diff-065145409c352805812a26bcd8495b7fa58f65f22fd0690a64df96841b68b3b5R1-R2): Added an empty `__init__.py` file to the `mail_processing` module.

## [0.1.1] - 2025-02-09
- Merged PR #2 by @MarcChen: Fix : run workflowissue
This pull request includes changes to the `services/oauth_credentials/config_creds.py` file to refactor the token-saving functionality and add command-line interface support.

Refactoring and CLI support:

* Encapsulated the token-saving logic into a `save_tokens` function and added an argument for the save directory.
* Added command-line interface support using `argparse` to allow users to specify the save directory for the tokens.
* Updated the scope in the `token_response` dictionary to include `https://www.googleapis.com/auth/drive`.

## [0.2.0] - 2025-02-09
- Merged PR #3 by @MarcChen: Feature : retrieve review data
This pull request includes several changes to the codebase, primarily focusing on refactoring, enhancing functionality, and improving maintainability. The most important changes include updating file paths for Google integration, removing an obsolete workflow, and enhancing email processing capabilities.

### Refactoring and File Path Updates:
* [`.github/workflows/run.yml`](diffhunk://#diff-a3ddd7238fc6e36daeb0ef76e93fe15cc87824bd3299888075210c5ca6a474d3L96-R96): Updated the script path for generating Google API tokens to use `services/google_integration/config_creds.py` instead of `services/oauth_credentials/config_creds.py`.
* `services/google_integration/calendar_services.py` and `services/google_integration/gmail_services.py`: Changed import paths from `oauth_credentials.authentification` to `services.google_integration.authentification`. [[1]](diffhunk://#diff-c7f9db28c79275a0e196974bd022be6e4429bb6f5559ff021e643c0425d9df51L10-R10) [[2]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L10-R11)

### Workflow Removal:
* [`.github/workflows/setup.yml`](diffhunk://#diff-21b2bb33643eb2ddec63535b53d81e3dbf12907d4ead032a90327495ff3e7641L1-L65): Removed the one-time setup workflow, which included steps for setting up the Node.js environment, creating labels, and configuring branch protection.

### Email Processing Enhancements:
* `services/google_integration/gmail_services.py`: 
  - Added a new label `review` and updated the `parse_reservation_header` method to handle review emails. [[1]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46R38) [[2]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L183-R213)
  - Updated the `process_unread_emails` method to tag review emails and modified methods to handle emails by label. [[1]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L207-R226) [[2]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46R236-R243) [[3]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L229-R271)
* `services/mail_processing/mail_processor.py`: 
  - Modified methods to use the new label-based email processing functions and added a quality check for reservations. [[1]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR14-R41) [[2]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR90-R137)
  - Introduced a new method `process_review_mails` to handle review emails and updated the workflow to include this step. [[1]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR171) [[2]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL152-L182) [[3]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL198-R252)

### Minor Adjustments:
* [`pyproject.toml`](diffhunk://#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711L7): Removed the specific inclusion of `oauth_credentials` from the `packages` list.This pull request includes several changes to improve the functionality and integration of Google services, as well as to enhance email processing and parsing. The most important changes include refactoring the Google API token generation, updating the email parsing logic, and adding new methods for handling email labels and processing review emails.

### Integration and Refactoring:

* [`.github/workflows/run.yml`](diffhunk://#diff-a3ddd7238fc6e36daeb0ef76e93fe15cc87824bd3299888075210c5ca6a474d3L96-R96): Updated the path for generating Google API tokens from `services/oauth_credentials/config_creds.py` to `services/google_integration/config_creds.py`.
* `services/google_integration/calendar_services.py` and `services/google_integration/gmail_services.py`: Changed import paths from `oauth_credentials.authentification` to `services.google_integration.authentification`. [[1]](diffhunk://#diff-c7f9db28c79275a0e196974bd022be6e4429bb6f5559ff021e643c0425d9df51L10-R10) [[2]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L10-R11)

### Email Parsing and Processing:

* [`services/google_integration/gmail_services.py`](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L183-R213): Enhanced the `parse_reservation_header` method to include review email parsing and updated the `process_unread_emails` method to handle review emails. [[1]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L183-R213) [[2]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L207-R226) [[3]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46R236-R243) [[4]](diffhunk://#diff-56e00a66c727615e2c7dc860090ab5b71b5e798314479f5137c9686478422c46L229-R271)
* [`services/mail_processing/mail_processor.py`](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR90-R137): Added methods for processing review emails and performing quality checks on reservations, and refactored existing methods to improve readability and functionality. [[1]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR90-R137) [[2]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR171) [[3]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL152-L182) [[4]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL198-R252)

### Workflow and Setup:

* [`.github/workflows/setup.yml`](diffhunk://#diff-21b2bb33643eb2ddec63535b53d81e3dbf12907d4ead032a90327495ff3e7641L1-L65): Removed the one-time setup workflow, which included setting up Node.js, creating labels, and configuring branch protection.

### Debugging and Enhancements:

* [`services/mail_processing/parser.py`](diffhunk://#diff-c08f5a1148c23251f9e5c8ac593a309758f3f8427c1119499d05f5f3c3a38949L13-R20): Added a `debug` parameter to the `Parser` class to facilitate debugging during email parsing.

## [0.2.1] - 2025-02-09
- Merged PR #4 by @MarcChen: Fix : Regexp and casting issue 
This pull request includes several updates to the `mail_processor.py` and `parser.py` files to improve debugging capabilities and simplify code.

### Debugging enhancements:

* Added a `debug` parameter to the `Parser` class within the `parse_reserved_mails` method to enhance debugging capabilities.
* Modified the `run_workflow` method to conditionally execute certain steps based on the `debug` flag, preventing unnecessary operations during debugging. [[1]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL231-R223) [[2]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL247-L270)

### Code simplification:

* Simplified the `fix_payout_value` method in `parser.py` by replacing a substring instead of using multiple string operations.
* Updated the regex pattern in the `get_language_patterns` method to handle additional cases for host payout parsing.

### Code reorganization:

* Reorganized imports in `mail_processor.py` for better readability and maintainability. [[1]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eL1) [[2]](diffhunk://#diff-461eeb680ac665674f514f3bf1a1bc583a620a9ac28854f873df69120275984eR9-R10)

### Removal of commented-out code:

* Removed unnecessary commented-out debugging code from the `parse_reserved_mails` method to clean up the codebase.
* Removed unused commented-out code related to saving reservations to CSV in the `run_workflow` method.

## [0.2.2] - 2025-02-09
- Merged PR #5 by @MarcChen: small fix - casting issue resolved
This pull request includes a significant change to the `fix_payout_value` method in `services/mail_processing/parser.py`. The update enhances the method's functionality by improving how numeric strings are cleaned and formatted.

Improvements to numeric string cleaning and formatting:

* [`services/mail_processing/parser.py`](diffhunk://#diff-c08f5a1148c23251f9e5c8ac593a309758f3f8427c1119499d05f5f3c3a38949L282-L294): The `fix_payout_value` method has been updated to remove thousands separators, ensure a single decimal point, and strip any non-digit or punctuation characters except for '.' and ','. This change improves the accuracy and reliability of the numeric string cleaning process.

## [0.3.0] - 2025-02-10
- Merged PR #6 by @MarcChen: Feature : adding blocked days data retrieval from ics calendar
This pull request introduces a new feature to fetch blocked days from an Airbnb iCal URL and push them to a Notion database. It includes changes to the workflow configuration, the addition of a new script, and corresponding unit tests.

### Workflow Configuration:

* [`.github/workflows/run.yml`](diffhunk://#diff-a3ddd7238fc6e36daeb0ef76e93fe15cc87824bd3299888075210c5ca6a474d3L90-R90): Updated the dependency installation command to include the `streamlit_app` and added a new job to retrieve blocked days from the iCal calendar and push them to Notion. [[1]](diffhunk://#diff-a3ddd7238fc6e36daeb0ef76e93fe15cc87824bd3299888075210c5ca6a474d3L90-R90) [[2]](diffhunk://#diff-a3ddd7238fc6e36daeb0ef76e93fe15cc87824bd3299888075210c5ca6a474d3R114-R123)

### New Script:

* [`services/dataviz/src/get_blocked_days.py`](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR1-R123): Added a new script to fetch blocked days from an Airbnb iCal URL and push them to a Notion database. This script includes functions to fetch blocked days, push them to Notion, and retrieve blocked days from Notion.

### Unit Tests:

* [`tests/unit/test_get_blocked_days.py`](diffhunk://#diff-21cf15e7e9321281ba643b9700bd643cbcc4fa2867332882e42498a39d3be8a7R1-R70): Added unit tests for the new script, including dummy classes and functions to simulate calendar events and responses.

## [0.3.1] - 2025-02-10
- Merged PR #7 by @MarcChen: Fix : fixed mail date retrieval
This pull request includes updates to data files and significant changes to the `parser.py` script in the `mail_processing` service. The changes involve adding new data entries and refactoring the initialization and date parsing logic in the parser.

### Data Updates:
* [`services/dataviz/data/df_blocked_days_cache.csv`](diffhunk://#diff-7e8c2a9a32c0f1b8365d445f789745135bce176a08fa8af6753c59d9462edec1R1-R15): Added new entries for blocked days, including details such as start and end dates, name, insert date, duration, blocked days, and month year.
* [`services/dataviz/data/df_notion_cache.csv`](diffhunk://#diff-539c58dee3675e49504f36d128896b82d5bbdfd6f913027facd60817d98f901eR1-R64): Added new entries for bookings, including details such as arrival and departure dates, fees, total cost, number of guests, and other booking information.

### Codebase Changes:
* `services/mail_processing/parser.py`: 
  * Removed unused imports (`csv`, `os`) to clean up the code.
  * Refactored `__init__` method to use a new `parse_mail_date` method for extracting the mail date from the 'Snippet' field, with a fallback to the 'Date' field. Added debug print statement for mail date. [[1]](diffhunk://#diff-c08f5a1148c23251f9e5c8ac593a309758f3f8427c1119499d05f5f3c3a38949L22-R22) [[2]](diffhunk://#diff-c08f5a1148c23251f9e5c8ac593a309758f3f8427c1119499d05f5f3c3a38949R35)
  * Added `parse_mail_date` method to extract the mail date from the 'Snippet' field to handle cases where the 'Date' field has a lag or incorrect year.
  * Removed the `append_booking_data_to_csv` and `confirmation_code_exists_in_csv` methods, simplifying the codebase by eliminating unused functions.

## [0.4.0] - 2025-05-18
- Merged PR #8 by @MarcChen: Feature/adding calendar events when consecutive days
This pull request introduces significant enhancements to the Google Calendar integration service, focusing on conflict detection, event management, and integration testing. Key changes include adding conflict detection for overlapping events, improving event creation logic, and introducing a robust integration testing framework.

### Enhancements to Google Calendar Event Management:
* **Conflict Detection and Handling**: Added logic to detect overlapping events and mark them with a `[CONFLICT]` prefix in the title. Conflict events include warnings in their descriptions and customized email reminders.
* **New Event Retrieval Methods**: Introduced `_retrieve_past_day_events`, `_retrieve_future_day_events`, and `_retrieve_events_by_proximity` methods to fetch events based on proximity to a reference date, enabling more granular event management.
* **Improved Event Deletion**: Enhanced the `delete_event` method with better documentation and error handling.

### Integration Testing Framework:
* **Integration Test Setup**: Added a new `tests/integration` directory with a README explaining how to run integration tests. These tests interact with real Google Calendar APIs and require valid credentials [[1]](diffhunk://#diff-a3fdc939eba6bf3f6c81027112cbc8595bdcef44801d2e9e10c276c2a58c306fR1-R34) [[2]](diffhunk://#diff-6ec5224a3ecfa5b56e1dce12620fffa868d0b50190add628982d3596085b7e9dR1).
* **Test Cases for Conflict Detection**: Created integration tests to validate conflict detection and event creation logic, ensuring proper handling of overlapping reservations.
* **Proximity-Based Event Retrieval Test**: Added tests to verify the functionality of the `_retrieve_events_by_proximity` method.

### Configuration and Documentation Updates:
* **Pytest Configuration**: Updated `pyproject.toml` to include pytest markers for integration tests and specify test file naming conventions.
* **Rich Library Import**: Added the `rich` library for improved logging and debugging. 

These changes enhance the robustness and reliability of the calendar service while ensuring thorough testing in real-world scenarios.

## [0.4.1] - 2025-07-20
- Merged PR #9 by @MarcChen: Fix/retrieval of blocked days
This pull request introduces logging enhancements to the `services/dataviz/src/get_blocked_days.py` script, making it easier to debug and monitor its execution. It also includes minor dependency updates in the `pyproject.toml` file.

### Logging Enhancements:
* Added a `logging` configuration to the script, including a logger setup with `DEBUG` level logging and a specific log format. (`services/dataviz/src/get_blocked_days.py`)
* Integrated informational and debug-level logging throughout the `fetch_blocked_days_from_airbnb_ical`, `push_blocked_days_to_notion`, and `fetch_blocked_days_from_notion` functions to log key events, such as data fetching, processing, and decision-making. [[1]](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR8-R35) [[2]](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR44) [[3]](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR72-R94) [[4]](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR104-R114) [[5]](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR127) [[6]](diffhunk://#diff-83d8c18ec021f089538fad23466845c703830e9ab32d71a1fd358ef2d3bcbc8aR136-R147)
* Replaced `print` statements with `logger.info` and `logger.error` for consistent logging, including exception handling.

### Dependency Updates:
* Updated the version specification for `lxml` to use a caret range (`^4.9.0`) for greater flexibility in dependency resolution. (`pyproject.toml`)
* Corrected the version specification for `pandas` to align with the caret range syntax. (`pyproject.toml`)

## [0.4.2] - 2025-09-21
- Merged PR #10 by @MarcChen: Fix/blocked days retrieval


## [0.4.3] - 2025-09-22
- Merged PR #11 by @MarcChen: refactor: remove pandas dependency and update data handling 


