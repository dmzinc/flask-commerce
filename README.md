# E-commerce API

## Overview
This is a Flask-based API for an e-commerce platform, featuring user authentication, product management, shopping cart functionality, order processing, and inventory management.

## Features

### User Management
- User registration and authentication
- Role-based access control (Admin, Customer)
- Secure password handling with hashing
- JWT-based authentication

### Product Management
- Create, read, update, and delete products
- Support for both physical and digital products
- Product categorization by type
- Product search functionality
- Stock tracking for physical products

### Shopping Cart
- Add and remove products
- Update quantities
- Calculate total prices
- Stock validation for physical products
- Cart persistence in session

### Order Processing
- Create and manage orders
- Support for returns with refund processing
- Support for product exchanges
- Order history tracking
- Admin approval workflow for returns/exchanges

### Inventory Management
- Real-time stock tracking for physical products
- Automatic stock updates on purchases
- Stock validation to prevent overselling
- Separate handling for digital products

---

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create and activate conda environment:
```bash
conda env create -f environment.yaml
conda activate ecommerce-api
```

### 3. Create a .env file in the root directory:
```bash
DATABASE_URL=postgresql://username:password@localhost:54
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
pytest
```
    