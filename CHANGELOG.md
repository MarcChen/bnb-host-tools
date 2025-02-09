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

