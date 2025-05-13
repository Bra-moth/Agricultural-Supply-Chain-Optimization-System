# Agricultural Supply Chain Optimization System

## Overview

The Agricultural Supply Chain Optimization System is a web-based platform designed to streamline the agricultural supply chain process by connecting farmers, distributors, and retailers. The system provides real-time tracking, inventory management, and analytics to optimize the flow of agricultural products from farm to market.

## Features

### For Farmers

- Crop inventory management
- Harvest tracking and scheduling
- Real-time market price monitoring
- Direct connection with distributors
- Sales analytics and reporting
- Order management system

### For Distributors

- Inventory management
- Order processing and tracking
- Route optimization
- Warehouse management
- Real-time delivery tracking
- Supply chain analytics

### For Retailers

- Product browsing and ordering
- Real-time stock availability
- Sales analytics and reporting
- Automated reordering system
- Order history tracking
- Market insights

## Technical Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Chart.js
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **File Handling**: Werkzeug

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/Agricultural-Supply-Chain-Optimization-System.git
cd Agricultural-Supply-Chain-Optimization-System
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Initialize the database:

```bash
python init_db.py
```

5. Run the application:

```bash
python app.py
```

## Configuration

- Database configuration in `app.py`
- File upload settings in `app.py`
- Security settings in `app.py`

## Project Structure

```
Agricultural-Supply-Chain-Optimization-System/
├── app.py                 # Main application file
├── models.py             # Database models
├── forms.py              # Form definitions
├── extensions.py         # Flask extensions
├── init_db.py           # Database initialization
├── requirements.txt      # Project dependencies
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
└── instance/            # Instance-specific files
```

## Default Users

The system comes with pre-configured test accounts:

1. Farmer Account:

   - Username: farmer_john
   - Password: farm123

2. Distributor Account:

   - Username: distributor_sam
   - Password: dist123

3. Retailer Account:
   - Username: retailer_mary
   - Password: retail123

## Security Features

- Password hashing using Werkzeug
- CSRF protection
- Role-based access control
- Secure file uploads
- Input validation

## Development Guidelines

1. Follow PEP 8 style guide for Python code
2. Use meaningful commit messages
3. Write tests for new features
4. Document code changes
5. Handle errors gracefully

## Error Handling

The system includes comprehensive error handling for:

- Database operations
- File operations
- Authentication
- Authorization
- Form validation
- API requests

## API Endpoints

The system provides several API endpoints for:

- Order management
- Inventory updates
- Market price updates
- Delivery tracking
- Analytics data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact:

- Email: support@agri-scm.com
- Phone: +27 123 456 789
- Location: Kimberley, Northern Cape, South Africa
