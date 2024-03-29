import sqlite3
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.uic import loadUi
from dotenv import load_dotenv

load_dotenv()


class FillDetailsWindow(QMainWindow):
    def __init__(self, username):
        super(FillDetailsWindow, self).__init__()

        # Load the .ui file
        loadUi('../UI/fill_details.ui', self)

        self.setWindowTitle("Fill Details")

        # Set the welcome message dynamically
        self.welcome_label.setText(f"Welcome, {username}! Please fill in your details.")

        # Connect the submit button to the submit_details method
        self.submit_button.clicked.connect(self.submit_details)

        # Save the username as an instance variable
        self.username = username

        # Update the users table if necessary
        self.update_users_table()

        # Load saved values
        self.load_saved_values(username)

        # Set default gender value to Male
        self.gender_input.setCurrentText("Male")

    def update_users_table(self):
        try:
            connection = sqlite3.connect("../database/signup.db")
            cursor = connection.cursor()

            # Check if the columns already exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            required_columns = ["full_name", "branch", "specialization", "phone", "gender"]  # Include 'gender'

            # Add the columns that do not exist
            for column in required_columns:
                if column not in columns:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
                    connection.commit()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def load_saved_values(self, username):
        try:
            connection = sqlite3.connect("../database/signup.db")
            cursor = connection.cursor()

            # Fetch user details from the database
            cursor.execute("SELECT full_name, branch, specialization, phone, gender FROM users WHERE name = ?", (username,))
            user_details = cursor.fetchone()

            if user_details:
                # Populate input fields with saved values
                full_name, branch, specialization, phone, gender = user_details
                self.full_name_input.setText(full_name)
                self.branch_input.setText(branch)
                self.specialization_input.setText(specialization)
                self.phone_input.setCurrentText(phone)
                self.gender_input.setCurrentText(gender)

            # Close the connection
            connection.close()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def submit_details(self):
        # Get the input values
        full_name = self.full_name_input.text()
        branch = self.branch_input.text()
        specialization = self.specialization_input.text()
        phone = self.phone_input.currentText()  # Get the currently selected option
        gender = self.gender_input.currentText()

        # Check if any required field is empty
        if not all([full_name, branch, specialization, phone, gender]):
            QMessageBox.warning(self, "Error", "Please fill in all details.")
            return

        # Connect to the database and update user details
        try:
            connection = sqlite3.connect("../database/signup.db")
            cursor = connection.cursor()

            # Update the user details in the database
            cursor.execute("UPDATE users SET full_name = ?, branch = ?, specialization = ?, phone = ?, gender = ? WHERE name = ?",
                           (full_name, branch, specialization, phone, gender, self.username))

            # Commit the transaction
            connection.commit()

            # Close the connection
            connection.close()

            # Display a success message
            QMessageBox.information(self, "Success", "User details updated successfully.")

            # Close the window after submitting details
            self.close()
        except sqlite3.Error as e:
            # Display an error message if there's an issue with the database
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
