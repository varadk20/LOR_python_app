import sqlite3
import re
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QApplication
from PyQt6.uic import loadUi
from LOR_python_app.code.adminwindow import AdminWindow
from LOR_python_app.code.errorwindow import ErrorWindow


class SignUpWindow(QMainWindow):
    def __init__(self):
        super(SignUpWindow, self).__init__()
        loadUi("../UI/signup.ui", self)
        self.pushButton.clicked.connect(self.on_signup_button_clicked)
        self.pushButton_2.clicked.connect(self.show_login_window)
        self.admin_button.clicked.connect(self.show_admin_window)
        self.lineEdit_3.setEchoMode(QLineEdit.EchoMode.Password)
        self.show()

    def show_admin_window(self):
        self.admin_window = AdminWindow()  # Create an instance of the AdminWindow
        self.admin_window.show()  # Show the AdminWindow


    def on_signup_button_clicked(self):
        from LOR_python_app.code.login import Login
        name = self.lineEdit.text()
        email = self.lineEdit_2.text()
        password = self.lineEdit_3.text()

        emailPattern = '[a-z0-9A-Z]*@student.sfit.ac.in'
        usernamePattern = '[a-z0-9A-Z_]*'
        if not re.match(emailPattern, email):
            error_message = "<font color='red'>Invalid credentials.Please enter college email address</font>"
            self.error_window = ErrorWindow(error_message)
            self.error_window.show()
            return

        if not re.match(usernamePattern, name):
            error_message = "<font color='red'>Please enter a combination from a-z,A-Z,0-9,_</font>"
            self.error_window = ErrorWindow(error_message)
            self.error_window.show()
            return

        if not name or not email or not password:
            error_message = "<font color='red'>Please fill in all fields.</font>"
            self.error_window = ErrorWindow(error_message)
            self.error_window.show()
            return

        # check if username already exists
        if self.check_username_exists(name):
            error_message = "<font color='red'>Username already exists. Please choose a different one.</font>"
            self.error_window = ErrorWindow(error_message)
            self.error_window.show()
            return

        # check if mail already exists
        if self.check_mail_exists(email):
            error_message = "<font color='red'>Email already exists. Please choose a different one.</font>"
            self.error_window = ErrorWindow(error_message)
            self.error_window.show()
            return

        # Store signup values in SQLite database
        if self.store_signup_data(name, email, password):
            self.close()  # Close the current window
            self.login_window = Login()
            self.login_window.show()

            print("Name:", name)
            print("Email:", email)
            print("Password:", password)



    def show_login_window(self):
        from LOR_python_app.code.login import Login
        self.close()
        self.login_window = Login()
        self.login_window.show()

    def store_signup_data(self, name, email, password):
        try:
            connection = sqlite3.connect("../database/signup.db")
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, email TEXT, password TEXT)")
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            connection.commit()
            return True
        except Exception as e:
            print("Error occurred while storing signup data:", e)
            return False

    def check_username_exists(self, username):
        try:
            connection = sqlite3.connect("../database/signup.db")
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE name = ?", (username,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print("Error occurred while checking username existence:", e)
            return False

    def check_mail_exists(self, mail):
        try:
            connection = sqlite3.connect("../database/signup.db")
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (mail,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print("Error occurred while checking username existence:", e)
            return False
