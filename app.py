from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_connection
from ml.recommendation import recommend_products

app = Flask(__name__)
app.secret_key = "product_recommendation_secret"

# ---------------- HOME ----------------

@app.route("/")
@app.route("/home")
def home():

    search = request.args.get("search", "").strip()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE title LIKE %s
               OR category LIKE %s
            LIMIT 50
            """,
            (
                f"%{search}%",
                f"%{search}%"
            )
        )

    else:

        cursor.execute(
            "SELECT * FROM products LIMIT 50"
        )

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "home.html",
        products=products
    )

# ---------------- PRODUCT DETAILS ----------------
@app.route("/product/<product_id>")
def product(product_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM products WHERE product_id=%s",
        (product_id,)
    )

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    # Generate recommendations
    recommendations = recommend_products(product_id)
    print("Product page opened")
    print(session)

    # Save recommendation log only if user is logged in
    # Save recommendation log only if user is logged in
    if "user_id" in session:

        print("Saving recommendation log...")

        recommended_ids = ",".join(
            [item["product_id"] for item in recommendations]
        )

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO recommendation_logs
                (user_id, product_id, recommended_products)
                VALUES (%s, %s, %s)
                """,
                (
                    session["user_id"],
                    product_id,
                    recommended_ids
                )
            )

            conn.commit()

            

        except Exception as e:

            print("DATABASE ERROR:")
            print(e)

        finally:

            cursor.close()
            conn.close()

    return render_template(
        "product.html",
        product=product,
        recommendations=recommendations
    )
# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET","POST"])

def login():

    if request.method=="POST":

        email=request.form["email"]

        password=request.form["password"]

        conn=get_connection()

        cursor=conn.cursor(dictionary=True)

        cursor.execute(

            """

            SELECT *

            FROM users

            WHERE email=%s

            AND password=%s

            """,

            (email,password)

        )

        user=cursor.fetchone()

        cursor.close()

        conn.close()

        if user:

            session["user_id"]=user["user_id"]

            session["user_name"]=user["name"]

            return redirect("/")

        flash("Invalid Email or Password")

    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])

def register():

    if request.method=="POST":

        name=request.form["name"]

        email=request.form["email"]

        password=request.form["password"]

        conn=get_connection()

        cursor=conn.cursor(dictionary=True)

        cursor.execute(

            "SELECT * FROM users WHERE email=%s",

            (email,)

        )

        existing_user=cursor.fetchone()

        if existing_user:

            flash("Email already registered!")

            cursor.close()

            conn.close()

            return redirect("/register")

        cursor.execute(

            """

            INSERT INTO users(name,email,password)

            VALUES(%s,%s,%s)

            """,

            (name,email,password)

        )

        conn.commit()

        cursor.close()

        conn.close()

        flash("Registration Successful!")

        return redirect("/login")

    return render_template("register.html")

# ---------------- CART ----------------

@app.route("/cart")
def cart():

    if "user_id" not in session:

        return redirect("/login")

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""

        SELECT

            cart_items.cart_item_id,

            products.product_id,

            products.title,

            products.price,

            products.image_url

        FROM cart_items

        JOIN products

        ON cart_items.product_id = products.product_id

        JOIN cart

        ON cart_items.cart_id = cart.cart_id

        WHERE cart.user_id=%s

    """,(session["user_id"],))

    items = cursor.fetchall()

    cursor.close()

    conn.close()

    return render_template("cart.html",items=items)

@app.route("/add_to_cart/<product_id>")
def add_to_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the user already has a cart
    cursor.execute(
        "SELECT * FROM cart WHERE user_id=%s",
        (session["user_id"],)
    )

    cart = cursor.fetchone()

    # Create a cart if it doesn't exist
    if cart is None:

        cursor.execute(
            """
            INSERT INTO cart(user_id)
            VALUES(%s)
            """,
            (session["user_id"],)
        )

        conn.commit()

        cursor.execute(
            "SELECT * FROM cart WHERE user_id=%s",
            (session["user_id"],)
        )

        cart = cursor.fetchone()

    # Check whether the product is already in the cart
    cursor.execute(
        """
        SELECT *
        FROM cart_items
        WHERE cart_id=%s
        AND product_id=%s
        """,
        (
            cart["cart_id"],
            product_id
        )
    )

    existing = cursor.fetchone()

    # Add only if it isn't already present
    if existing is None:

        cursor.execute(
            """
            INSERT INTO cart_items(cart_id, product_id)
            VALUES(%s, %s)
            """,
            (
                cart["cart_id"],
                product_id
            )
        )

        conn.commit()

    cursor.close()
    conn.close()

    return redirect("/cart")

@app.route("/remove_from_cart/<int:cart_item_id>")
def remove_from_cart(cart_item_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM cart_items WHERE cart_item_id=%s",
        (cart_item_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/cart")

# -------------------- Log out --------------

@app.route("/logout")

def logout():

    session.clear()

    return redirect("/")
# ---------------- RUN ----------------

if __name__ == "__main__":

    app.run(debug=True)