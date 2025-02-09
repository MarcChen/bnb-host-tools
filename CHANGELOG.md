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

