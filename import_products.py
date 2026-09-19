import pandas as pd
import re
from database.db import get_connection

# Read CSV
df = pd.read_csv("products.csv")

# Fill missing values
df.fillna("", inplace=True)

def clean_price(price):
    """
    Extract the first valid decimal number from any messy price string.
    Examples:
    '$237.68' -> 237.68
    '6.94  6 . 94' -> 6.94
    '$1,299.99' -> 1299.99
    '' -> 0.0
    """
    price = str(price)

    # Remove commas
    price = price.replace(",", "")

    # Find first decimal/integer number
    match = re.search(r"\d+(\.\d+)?", price)

    if match:
        return float(match.group())

    return 0.0

# Clean price column
df["price"] = df["price"].apply(clean_price)

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DELETE FROM products")

for _, row in df.iterrows():

    cursor.execute("""
        INSERT INTO products
        (product_id,title,description,category,price,image_url)
        VALUES (%s,%s,%s,%s,%s,%s)
    """,(
        str(row["product_id"]),
        row["title"],
        row["description"],
        row["category"],
        row["price"],
        row["image_url"]
    ))

conn.commit()

print("✅ Products Imported Successfully!")

cursor.close()
conn.close()