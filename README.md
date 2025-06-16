# PinnacleWeb Backend

## Overview
The PinnacleWeb Backend is the server-side application that powers the PinnacleWeb platform. It provides APIs, handles business logic, and manages data storage.

## Features
- RESTful API endpoints
- Database integration
- Authentication and authorization
- Error handling and logging

## Requirements
- Python 3.8+
- MySQL Server
- Virtual environment (recommended)

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/leshfayisa/pinnacle-backend-app.git
    cd pinnacle-backend-app
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration
1. Create a `.env` file in the root directory.
2. Add the following environment variables:
    ```
    SECRET_KEY=your_secret_key_here
    MYSQL_HOST=localhost
    MYSQL_USER=root
    MYSQL_PASSWORD=your_mysql_password
    MYSQL_DB=your_database_name
    ```

## Usage
Create Virtual Environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install Dependencies:
```bash
pip install -r requirements.txt
```
Database Setup:

Open the database.md file in the project root.
Copy and run the SQL queries using your MySQL client to create the necessary tables and schema

Start the development server:
```bash
python app.py
```



## 🔒 License

This project is **private and proprietary**.  
**You are not allowed to copy, redistribute, or reuse any part of this code without explicit permission from the author.**

---

## 🚫 Contributing

This is a personal or internal project. External contributions are **not accepted**.
