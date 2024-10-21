Here's the complete README content formatted in Markdown for your `README.md` file:

````markdown
# Application README

## Overview

This application provides a comprehensive API for managing payments and splits. It allows users to register, log in, view and manage their payments, and generate balance sheets.

## Getting Started

To run this application, follow these steps:

### Running the Application

For **Windows**:

1. Run the `run.bat` file by double-clicking it or executing it in the command prompt.

For **macOS/Linux**:

1. Run the `run.sh` file by executing it in the terminal:
   ```bash
   sh run.sh
   ```
````

### Troubleshooting

If you encounter any issues while running the application:

1. Ensure Python is installed. If not, please download and install it from [python.org](https://www.python.org/downloads/).
2. The script will automatically create a virtual environment and install the required packages from `requirements.txt`.
3. If you need to create the virtual environment manually, run:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - For Windows:
     ```bash
     venv\Scripts\activate
     ```
   - For macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
5. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
6. Finally, run the application:
   ```bash
   python app.py
   ```

## API Documentation

The API documentation is available at the root route (`/`).

### Available Routes

1. **GET `/apiCheck`**: Checks the status of the API.
2. **POST `/api/register`**: Registers a new user in the system.
3. **POST `/api/login`**: Logs in a user and returns a JWT token.
4. **GET `/api/search/<string:search>`**: Searches for users by name or email.
5. **GET `/api/payments`**: Retrieves all payments for the authenticated user.
6. **POST `/api/payments`**: Adds a new payment with split details.
7. **DELETE `/api/payments`**: Deletes a specific payment and all associated splits.
8. **GET `/api/user`**: Retrieves the details of the authenticated user.
9. **GET `/api/splits`**: Retrieves all splits involving the current user.
10. **GET `/api/download_balance_sheet`**: Generates an Excel sheet including all payments and splits, with options to download the balance sheet.

## Conclusion

Follow these instructions to get the application running smoothly. For any further issues, please check the respective scripts or contact support.
