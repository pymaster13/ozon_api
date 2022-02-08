# OZON API

This project is realized for a customer-seller on OZON (2021). 

## Getting Started
Python version: 3.8.10

Clone project:
```
git clone https://github.com/pymaster13/ozon_api.git && cd ozon_api
```

Create and activate virtual environment:
```
python3 -m venv venv && source venv/bin/activate
```

Install libraries:
```
python3 -m pip install -r requirements.txt
```

Run local Django server:
```
python3 manage.py runserver
```

## Functional

At the input: links to products from the customer's store.

Functionality (performs a certain period of time):
- Analysis of the OZON store for a specific product and finding the minimum price for it;
- Setting the price for this product, which is one unit less than the one found, so that when sorting by the lowest price, the product offered by the customer is in 1st place;
- Bypass Captcha, etc.

At the exit: JSON with minimum prices for relevant products.

### Features

Main libraries that are used : 
- Django 3,
- djangorestframework,
- beautifulsoup4, lxml (for parsing html), 
- selenium (for imitation of user actions),
- logging (for logging all work processes).
