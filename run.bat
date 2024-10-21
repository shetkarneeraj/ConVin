@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Check if Python is installed
where python >nul 2>nul
IF ERRORLEVEL 1 (
    echo Python is not installed. Please install Python from https://www.python.org/downloads/.
    exit /b 1
) ELSE (
    echo Python is installed. Proceeding...
)

:: Create a virtual environment
echo.
echo Creating a virtual environment...
python -m venv venv
IF ERRORLEVEL 1 (
    echo Failed to create a virtual environment. Please check your Python installation.
    exit /b 1
) ELSE (
    echo Virtual environment created successfully.
)

:: Activate the virtual environment
call venv\Scripts\activate.bat
IF ERRORLEVEL 1 (
    echo Failed to activate the virtual environment. Please check the venv directory.
    exit /b 1
)

:: Install requirements
echo.
echo Installing requirements from requirements.txt...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo Failed to install requirements. Please check the requirements.txt file.
    exit /b 1
) ELSE (
    echo Requirements installed successfully.
)

:: Run the app
echo.
echo Running app.py...
python app.py
IF ERRORLEVEL 1 (
    echo Failed to run app.py. Please check your application for errors.
    exit /b 1
)

echo.
echo Setup completed successfully!
ENDLOCAL
