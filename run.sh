#!/bin/bash

# Function to print messages
echo_message() {
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo_message "Python is installed. Proceeding..."
else
    echo_message "Python is not installed. Please install Python from https://www.python.org/downloads."
    exit 1
fi

# Create a virtual environment
echo_message "Creating a virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo_message "Failed to create a virtual environment. Please check your Python installation."
    exit 1
else
    echo_message "Virtual environment created successfully."
fi

# Activate the virtual environment
echo_message "Activating the virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo_message "Failed to activate the virtual environment. Please check the venv directory."
    exit 1
fi

# Install requirements
echo_message "Installing requirements from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo_message "Failed to install requirements. Please check the requirements.txt file."
    exit 1
else
    echo_message "Requirements installed successfully."
fi

# Run the app
echo_message "Running app.py..."
python app.py
if [ $? -ne 0 ]; then
    echo_message "Failed to run app.py. Please check your application for errors."
    exit 1
fi

echo_message "Setup completed successfully!"
