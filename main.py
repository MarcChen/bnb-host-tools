from services.mail_processing.mail_processor import MailProcessorService

if __name__ == "__main__":
    processor = MailProcessorService()
    processor.run_workflow()
