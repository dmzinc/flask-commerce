# E-commerce API

## Overview
This is a Flask-based API for an e-commerce platform, featuring user authentication, product management, shopping cart functionality, order processing, and inventory management.

## Installation

### 1. Clone the Repository```bash
git clone https://github.com/dmzinc/flask-commerce.git
cd flask-commerce```

### 2. Create and activate conda environment:
```bash
conda env create -f env.yaml
conda activate ecommerce
```

### 3. Create a .env file in the root directory:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
JWT_SECRET_KEY=your_secret_key
```

### 4. Initialize the database:
```bash
python main.py
```

### 5. Run the application:
```bash
python main.py
```

### 6. Run tests:
```bash
pytest tests/
```
    

