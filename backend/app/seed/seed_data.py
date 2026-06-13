"""
Seed data generator for XenoCRM.

Generates 500 realistic BrewBox (coffee chain) customers with Indian
names, 8 cities, and believable purchase patterns. Each customer gets
1-12 orders with BrewBox menu items.

Usage:
    python -m app.seed.seed_data          # run directly
    Called from main.py on first startup   # automatic
"""

import asyncio
import random
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select, func as sa_func

from app.core.database import async_session_maker, init_db
from app.models.customer import Customer
from app.models.order import Order


# ═══════════════════════════════════════════════════════════════════
# REALISTIC INDIAN NAME DATA
# ═══════════════════════════════════════════════════════════════════

FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav",
    "Advaith", "Aryan", "Dhruv", "Kabir", "Ritvik", "Aarush", "Kian",
    "Darsh", "Veer", "Harsh", "Rohan", "Yash", "Mihir", "Kartik", "Neil",
    "Sahil", "Aman", "Raghav", "Vikram", "Kunal", "Manav", "Dev", "Arnav",
    "Tejas", "Gaurav", "Siddharth", "Ankit", "Parth", "Ishan", "Nikhil",
    "Akash", "Rahul", "Varun", "Tarun", "Nishant", "Aakash",
]

FIRST_NAMES_FEMALE = [
    "Saanvi", "Aanya", "Aadhya", "Aaradhya", "Ananya", "Pari", "Anika",
    "Navya", "Diya", "Myra", "Sara", "Ira", "Ahana", "Prisha", "Riya",
    "Anvi", "Aisha", "Kiara", "Meera", "Tara", "Nisha", "Kavya", "Shreya",
    "Pooja", "Neha", "Priya", "Simran", "Tanvi", "Ishita", "Kritika",
    "Divya", "Sneha", "Aanchal", "Sakshi", "Radhika", "Megha", "Pallavi",
    "Sanya", "Ritika", "Trisha", "Vanya", "Zara", "Rhea", "Sia", "Mahi",
    "Avni", "Nandini", "Charvi", "Aditi", "Khushi",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Joshi",
    "Reddy", "Nair", "Iyer", "Menon", "Rao", "Das", "Bose", "Sen",
    "Chatterjee", "Banerjee", "Mukherjee", "Malhotra", "Kapoor",
    "Agarwal", "Mehta", "Shah", "Jain", "Chopra", "Thakur", "Pillai",
    "Desai", "Naidu", "Srinivasan", "Kulkarni", "Patil", "Deshmukh",
    "Saxena", "Tiwari", "Pandey", "Mishra", "Dubey", "Chauhan",
    "Bhatt", "Kaur", "Gill", "Bhatia", "Khanna", "Bajaj", "Sinha",
    "Dutta", "Ghosh", "Roy", "Sethi",
]

# ═══════════════════════════════════════════════════════════════════
# GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════

CITIES = [
    "Mumbai",
    "Delhi",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Jaipur",
]

# Weighted distribution — metros get more customers.
CITY_WEIGHTS = [0.20, 0.18, 0.18, 0.12, 0.10, 0.10, 0.07, 0.05]

# ═══════════════════════════════════════════════════════════════════
# BREWBOX MENU — realistic Indian coffee chain pricing (INR)
# ═══════════════════════════════════════════════════════════════════

MENU_ITEMS = [
    {"name": "Cappuccino", "price": 249},
    {"name": "Cold Brew", "price": 299},
    {"name": "Latte", "price": 269},
    {"name": "Espresso", "price": 199},
    {"name": "Americano", "price": 219},
    {"name": "Mocha", "price": 289},
    {"name": "Flat White", "price": 279},
    {"name": "Cortado", "price": 229},
    {"name": "Affogato", "price": 319},
    {"name": "Iced Caramel Latte", "price": 329},
    {"name": "Matcha Latte", "price": 309},
    {"name": "Hot Chocolate", "price": 239},
    {"name": "Chai Latte", "price": 229},
    {"name": "Nitro Cold Brew", "price": 349},
    {"name": "Filter Coffee", "price": 179},
    {"name": "Hazelnut Cappuccino", "price": 299},
    {"name": "Vanilla Cold Brew", "price": 319},
    {"name": "Turmeric Latte", "price": 269},
    # Food items
    {"name": "Croissant", "price": 169},
    {"name": "Blueberry Muffin", "price": 149},
    {"name": "Avocado Toast", "price": 299},
    {"name": "Paneer Puff", "price": 129},
    {"name": "Chocolate Brownie", "price": 179},
    {"name": "Veg Club Sandwich", "price": 249},
    {"name": "Banana Bread", "price": 159},
    {"name": "Cookie (Choco Chip)", "price": 99},
]

# ═══════════════════════════════════════════════════════════════════
# EMAIL DOMAIN PATTERNS
# ═══════════════════════════════════════════════════════════════════

EMAIL_DOMAINS = [
    "gmail.com", "gmail.com", "gmail.com",  # weighted towards gmail
    "yahoo.co.in", "outlook.com", "hotmail.com",
    "rediffmail.com", "icloud.com",
]

# ═══════════════════════════════════════════════════════════════════
# GENERATOR FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

# Track used phone numbers and emails to guarantee uniqueness.
_used_phones: set[str] = set()
_used_emails: set[str] = set()


def _generate_phone() -> str:
    """Generate a unique 10-digit Indian mobile number starting with 7/8/9."""
    while True:
        prefix = random.choice(["7", "8", "9"])
        number = prefix + "".join(str(random.randint(0, 9)) for _ in range(9))
        if number not in _used_phones:
            _used_phones.add(number)
            return number


def _generate_email(first: str, last: str, idx: int) -> str:
    """
    Generate a unique email address from name parts.

    Uses several common patterns (first.last, firstlast, first+digits)
    and appends the customer index as a fallback for uniqueness.
    """
    domain = random.choice(EMAIL_DOMAINS)
    first_l = first.lower()
    last_l = last.lower()

    patterns = [
        f"{first_l}.{last_l}",
        f"{first_l}{last_l}",
        f"{first_l}.{last_l}{random.randint(1, 99)}",
        f"{first_l}{random.randint(10, 999)}",
        f"{first_l}_{last_l}",
    ]
    base = random.choice(patterns)
    email = f"{base}@{domain}"

    # Guarantee uniqueness by appending index if collision occurs.
    if email in _used_emails:
        email = f"{first_l}.{last_l}{idx}@{domain}"
    _used_emails.add(email)
    return email


def _generate_name() -> tuple[str, str, str]:
    """Return (first_name, last_name, full_name) with random gender."""
    if random.random() < 0.5:
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)
    last = random.choice(LAST_NAMES)
    return first, last, f"{first} {last}"


def _generate_order_items() -> tuple[list[dict[str, Any]], float]:
    """
    Generate a realistic order: 1-4 items, return (items_list, total).

    Most orders are 1-2 items (quick coffee run), occasionally 3-4
    items (friends grabbing coffee together or coffee + food combo).
    """
    # Weighted item count: mostly 1-2 items
    num_items = random.choices([1, 2, 3, 4], weights=[40, 35, 18, 7])[0]
    chosen = random.sample(MENU_ITEMS, min(num_items, len(MENU_ITEMS)))

    items = []
    total = 0.0
    for item in chosen:
        qty = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
        items.append({
            "name": item["name"],
            "qty": qty,
            "price": item["price"],
        })
        total += item["price"] * qty

    return items, round(total, 2)


def _generate_customers_and_orders(
    count: int = 500,
) -> tuple[list[dict[str, Any]], list[list[dict[str, Any]]]]:
    """
    Generate `count` customers and their orders.

    Returns:
        customers: list of customer dicts (without id — DB assigns that).
        all_orders: list of order lists (index-aligned with customers).

    Spend patterns:
        - 60% regular shoppers:  1-4 orders,  spend ₹200–₹2,000
        - 25% loyalists:         5-8 orders,  spend ₹2,000–₹8,000
        - 15% VIPs:              8-12 orders,  spend ₹5,000–₹20,000
    """
    # Clear uniqueness trackers for idempotent re-runs.
    _used_phones.clear()
    _used_emails.clear()

    customers: list[dict[str, Any]] = []
    all_orders: list[list[dict[str, Any]]] = []

    # Date range for orders: last 6 months.
    today = date.today()
    start_date = today - timedelta(days=180)

    for i in range(count):
        first, last, full_name = _generate_name()
        phone = _generate_phone()
        email = _generate_email(first, last, i)
        city = random.choices(CITIES, weights=CITY_WEIGHTS)[0]

        # Determine customer tier for realistic spend distribution.
        tier_roll = random.random()
        if tier_roll < 0.60:
            # Regular shopper
            num_orders = random.randint(1, 4)
        elif tier_roll < 0.85:
            # Loyalist
            num_orders = random.randint(5, 8)
        else:
            # VIP
            num_orders = random.randint(8, 12)

        # Generate orders for this customer.
        orders = []
        total_spend = 0.0
        last_purchase = start_date

        for _ in range(num_orders):
            items, amount = _generate_order_items()
            # Random date within the 6-month window, sorted chronologically later.
            order_date = start_date + timedelta(
                days=random.randint(0, (today - start_date).days)
            )
            orders.append({
                "amount": amount,
                "items": items,
                "created_at": datetime.combine(order_date, datetime.min.time()),
            })
            total_spend += amount
            if order_date > last_purchase:
                last_purchase = order_date

        # Sort orders chronologically.
        orders.sort(key=lambda o: o["created_at"])

        customers.append({
            "name": full_name,
            "phone": phone,
            "email": email,
            "city": city,
            "total_spend": round(total_spend, 2),
            "order_count": num_orders,
            "last_purchase_date": last_purchase,
        })
        all_orders.append(orders)

    return customers, all_orders


# ═══════════════════════════════════════════════════════════════════
# DATABASE SEEDER
# ═══════════════════════════════════════════════════════════════════

async def seed_database() -> None:
    """
    Populate the database with 500 customers and their orders.

    Skips seeding if customers already exist (idempotent).
    Uses batch inserts for performance.
    """
    # Ensure tables exist.
    await init_db()

    async with async_session_maker() as session:
        # Check if data already exists.
        result = await session.execute(select(sa_func.count(Customer.id)))
        existing_count = result.scalar_one()

        if existing_count > 0:
            print(f"⏭  Database already has {existing_count} customers — skipping seed.")
            return

        print("🌱 Seeding database with 500 BrewBox customers...")

        customers_data, all_orders_data = _generate_customers_and_orders(500)

        # Batch insert customers first, then orders.
        customer_objects: list[Customer] = []
        for cust_data in customers_data:
            customer = Customer(**cust_data)
            session.add(customer)
            customer_objects.append(customer)

        # Flush to assign IDs before creating orders.
        await session.flush()

        order_count = 0
        for customer, orders_data in zip(customer_objects, all_orders_data):
            for order_data in orders_data:
                order = Order(
                    customer_id=customer.id,
                    **order_data,
                )
                session.add(order)
                order_count += 1

        await session.commit()

        print(f"✅ Seeded {len(customer_objects)} customers and {order_count} orders.")
        print("   Cities: " + ", ".join(CITIES))
        print(f"   Menu items: {len(MENU_ITEMS)} BrewBox products")


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    asyncio.run(seed_database())
