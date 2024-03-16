import os
import smtplib
from email.message import EmailMessage

from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt6.uic import loadUi
import sqlite3


class DatabaseWindow(QMainWindow):
    def __init__(self, data):
        super(DatabaseWindow, self).__init__()
        loadUi("../UI/database.ui", self)
        self.setWindowTitle("Database Contents")

        # Database initialization
        self.db_connection = sqlite3.connect("../database/signup.db")
        self.cursor = self.db_connection.cursor()

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(10, 10, 950, 600)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(9)  # Set the number of columns including the delete button and LOR button

        # Set column names
        column_names = ["username", "email", "password", "full-name", "branch", "specialization", "Phone",
                        "Generate LOR", "Delete"]
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
            self.tableWidget.setCellWidget(row_num, 8, delete_button)

            # Add "Generate LOR" button to the last column of each row
            generate_lor_button = QPushButton("Generate LOR")
            generate_lor_button.clicked.connect(lambda _, row=row_num: self.generate_lor(row))
            self.tableWidget.setCellWidget(row_num, 7, generate_lor_button)

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
            # Read the letter format from a text file
            with open("../LOR.txt", "r") as file:
                letter_format = file.read()

            # Get user details from the table
            username = self.tableWidget.item(row, 0).text()
            full_name = self.tableWidget.item(row, 3).text()
            branch = self.tableWidget.item(row, 4).text()
            specialization = self.tableWidget.item(row, 5).text()
            phone = self.tableWidget.item(row, 6).text()

            # Fill in the placeholders in the letter format with user details
            recommendation_content = letter_format.format(
                full_name=full_name,
                branch=branch,
                specialization=specialization,
                phone=phone,
                username=username
            )

            # Specify the folder path for saving the recommendation letters
            folder_path = "../All_LORs"
            os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist

            # Save the recommendation letter to a file in the "All_LORs" folder
            file_path = os.path.join(folder_path, f"{full_name}_LOR.txt")
            with open(file_path, "w") as file:
                file.write(recommendation_content)

            QMessageBox.information(self, "Recommendation Letter Generated",
                                    "The recommendation letter has been generated and saved.")

            # Send the generated recommendation letter via email
            recipient_email = self.tableWidget.item(row, 1).text()  # Assuming email is in the second column
            self.send_email(recipient_email, file_path)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"An error occurred while generating or sharing the recommendation letter: {str(e)}")

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
