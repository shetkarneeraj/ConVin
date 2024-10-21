Application README

Overview

This application provides a comprehensive API for managing payments and splits. It allows users to register, log in, view and manage their payments, and generate balance sheets.

Getting Started

To run this application, follow these steps:

Running the Application
For Windows:

Run the run.bat file by double-clicking it or executing it in the command prompt.
For macOS/Linux:

Run the run.sh file by executing it in the terminal:
bash
Copy code
sh run.sh
Troubleshooting
If you encounter any issues while running the application:

Ensure Python is installed. If not, please download and install it from python.org.
The script will automatically create a virtual environment and install the required packages from requirements.txt.
If you need to create the virtual environment manually, run:
bash
Copy code
python -m venv venv
Activate the virtual environment:
For Windows:
bash
Copy code
venv\Scripts\activate
For macOS/Linux:
bash
Copy code
source venv/bin/activate
Install the required packages:
bash
Copy code
pip install -r requirements.txt
Finally, run the application:
bash
Copy code
python app.py
API Documentation

The API documentation is available at the root route (/).

Available Routes
GET /apiCheck: Checks the status of the API.
POST /api/register: Registers a new user in the system.
POST /api/login: Logs in a user and returns a JWT token.
GET /api/search/<string:search>: Searches for users by name or email.
GET /api/payments: Retrieves all payments for the authenticated user.
POST /api/payments: Adds a new payment with split details.
DELETE /api/payments: Deletes a specific payment and all associated splits.
GET /api/user: Retrieves the details of the authenticated user.
GET /api/splits: Retrieves all splits involving the current user.
GET /api/download_balance_sheet: Generates an Excel sheet including all payments and splits, with options to download the balance sheet.
