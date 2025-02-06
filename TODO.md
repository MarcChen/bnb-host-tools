# TODO List

## Development
- [ ] Validate PR workflow with Black, isort, and Flake8
- [ ] Add some rich in the running workflows
- [ ] Make the parser works over all the already existing mails
- [ ] Factoriser le code parser !!! 
        - Faire une fonction Prendre en input les regexps, et ensuite fait tout le reste pour alimenter directement data + ADD cleaning_fee_regex = re.compile(
    r"(?<=Cleaning\sfee\r\n\r\n)€\s([\d\,\.]+)", 
    re.IGNORECASE
        - Faire des regexp communs reutilistable typiquement ([\d\,\.]+)
        - Nommer les groupes catché
)
- [ ] Mark as read after processed mails
- [ ] Add a method to check wether a row already exist in notion DB, otherwise append to it 
- [ ] Create the django Webserver to display the feature (based on Notion DB)
- [ ] Add more detailed workflows chart

## Additional Tasks
- [ ] Implement integration tests for core functionality
- [ ] Impelment unit tests
- [ ] Enhance error handling and assertions
- [ ] Update documentation for improved developer onboarding
- [ ] Handle cases when we recieve Canceled Reservation ! 