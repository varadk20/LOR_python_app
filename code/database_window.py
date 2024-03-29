import os
import sqlite3
import smtplib
from email.message import EmailMessage
from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt6.uic import loadUi
from docx import Document
from nlp import get_branch_similarity

class DatabaseWindow(QMainWindow):
    def __init__(self, data):
        super(DatabaseWindow, self).__init__()
        loadUi("../UI/database.ui", self)
        self.setWindowTitle("Database Contents")

        # Database initialization
        self.db_connection = sqlite3.connect("../database/signup.db")
        self.cursor = self.db_connection.cursor()

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(10, 10, 1150, 600)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(11)  # Increase the column count to accommodate the Reject button

        # Set column names
        column_names = ["username", "email", "password", "full-name", "branch", "specialization", "Requirement",
                        "Gender","Generate LOR", "Reject", "Delete"]
        self.tableWidget.setHorizontalHeaderLabels(column_names)

        self.populate_table(data)

    def populate_table(self, data):
        self.tableWidget.setRowCount(len(data))

        # Populate table with data
        for row_num, row_data in enumerate(data):
            for col_num, cell_data in enumerate(row_data):
                self.tableWidget.setItem(row_num, col_num, QTableWidgetItem(str(cell_data)))

            # Add delete button to the second last column of each row
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, row=row_num: self.delete_row(row))
            self.tableWidget.setCellWidget(row_num, 10, delete_button)

            # Add "Generate LOR" button to the second last column of each row
            generate_lor_button = QPushButton("Generate LOR")
            generate_lor_button.clicked.connect(lambda _, row=row_num: self.generate_lor(row))
            self.tableWidget.setCellWidget(row_num, 8, generate_lor_button)

            # Add "Reject" button to the last column of each row
            reject_button = QPushButton("Reject")
            reject_button.clicked.connect(lambda _, row=row_num: self.reject_application(row))
            self.tableWidget.setCellWidget(row_num, 9, reject_button)

    def reject_application(self, row):
        try:
            # Get user email from the table
            recipient_email = self.tableWidget.item(row, 1).text()  # Assuming email is in the second column

            # Send rejection email
            self.send_rejection_email(recipient_email)

            QMessageBox.information(self, "Application Rejected",
                                    "The application has been rejected. An email notification has been sent.")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"An error occurred while sending the rejection email: {str(e)}")

    def send_rejection_email(self, recipient_email):
        try:
            # Set up the rejection email message
            msg = EmailMessage()
            msg['Subject'] = 'Application Rejection'
            msg['From'] = os.getenv('MY_MAIL')  # Sender's email
            msg['To'] = recipient_email
            msg.set_content('Dear Applicant,\n\nYour application has been rejected. '
                            'If you have any questions, please contact the authority.')

            # Connect to the SMTP server and send the email
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(os.getenv('MY_MAIL'), os.getenv('PASSWORD'))
                smtp.send_message(msg)
        except Exception as e:
            raise e  # Handle the exception appropriately in your application

    def delete_row(self, row):
        # Get username of the row to be deleted
        username = self.tableWidget.item(row, 0).text()
        print("Deleting user:", username)

        # Remove row from the table
        self.tableWidget.removeRow(row)

        # Delete corresponding row from the database
        self.cursor.execute("DELETE FROM users WHERE name = ?", (username,))
        self.db_connection.commit()

    def generate_lor(self, row):
        try:
            # Get the value in the 6th column (Requirement)
            requirement = self.tableWidget.item(row, 6).text()

            # Select the appropriate letter format based on the requirement
            if requirement == "Higher Studies":
                letter_template_path = "../LOR.docx"
            elif requirement == "Professional":
                letter_template_path = "../LOR1.docx"
            else:
                QMessageBox.warning(self, "Invalid Requirement",
                                    "Requirement must be either 'Higher Studies' or 'Professional'.")
                return

            # Open the letter template
            doc = Document(letter_template_path)

            # Get user details from the table
            username = self.tableWidget.item(row, 0).text()
            full_name = self.tableWidget.item(row, 3).text()
            branch = self.tableWidget.item(row, 4).text()
            specialization = self.tableWidget.item(row, 5).text()
            phone = self.tableWidget.item(row, 6).text()
            gender = self.tableWidget.item(row, 7).text()

            # Determine the most similar predefined branch
            selected_branch = get_branch_similarity(branch)

            # Determine pronouns based on the gender
            if gender.lower() == "male":
                he_or_she = "he"
                his_or_her = "his"
                him_or_her = "him"
            else:
                he_or_she = "she"
                his_or_her = "her"
                him_or_her = "her"

            # Get the admin username
            admin_username = self.fetch_admin_username()

            # Fill in the placeholders in the letter template with user details and pronouns
            for paragraph in doc.paragraphs:
                if "{full_name}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{full_name}", full_name)
                if "{branch}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{branch}", branch)
                if "{specialization}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{specialization}", specialization)
                if "{phone}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{phone}", phone)
                if "{username}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{username}", username)
                if "{admin_username}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{admin_username}", admin_username)
                # Add pronouns
                if "{he_or_she}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{he_or_she}", he_or_she)
                if "{his_or_her}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{his_or_her}", his_or_her)
                if "{him_or_her}" in paragraph.text:
                    paragraph.text = paragraph.text.replace("{him_or_her}", him_or_her)

            # Specify the folder path for saving the recommendation letters
            folder_path = f"../All_LORs/{selected_branch}"
            os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist

            # Save the recommendation letter as a Word document
            file_path = os.path.join(folder_path, f"{full_name}_LOR.docx")
            doc.save(file_path)

            QMessageBox.information(self, "Recommendation Letter Generated",
                                    "The recommendation letter has been generated and saved.")

            # Send the generated recommendation letter via email
            recipient_email = self.tableWidget.item(row, 1).text()  # Assuming email is in the second column
            self.send_email(recipient_email, file_path)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"An error occurred while generating or sharing the recommendation letter: {str(e)}")

    def fetch_admin_username(self):
        try:
            # Connect to the admin.db database
            admin_db_connection = sqlite3.connect("../database/admin.db")
            admin_cursor = admin_db_connection.cursor()

            # Fetch the admin username from admin.db
            admin_cursor.execute("SELECT username FROM admins LIMIT 1")
            admin_username = admin_cursor.fetchone()[0]  # Fetch the first row and extract the username

            # Close the admin database connection
            admin_db_connection.close()

            return admin_username
        except Exception as e:
            print("Error fetching admin username:", e)

    def send_email(self, recipient_email, attachment_path):
        try:
            # Set up the email message
            msg = EmailMessage()
            msg['Subject'] = 'Recommendation Letter'
            msg['From'] = os.getenv('MY_MAIL')  # Sender's email
            msg['To'] = recipient_email
            msg.set_content('Please find the attached recommendation letter.')

            # Attach the recommendation letter file
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream',
                               filename=os.path.basename(attachment_path))

            # Connect to the SMTP server and send the email
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(os.getenv('MY_MAIL'), os.getenv('PASSWORD'))
                smtp.send_message(msg)

            QMessageBox.information(self, "Email Sent",
                                    "The recommendation letter has been sent via email.")

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"An error occurred while sending the email: {str(e)}")

    def closeEvent(self, event):
        self.db_connection.close()