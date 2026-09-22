from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import conn, cursor

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# =========================
# HOME
# =========================
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# =========================
# USER LOGIN PAGE
# =========================
@app.get("/user/login")
def user_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user_login.html",
        context={}
    )


# =========================
# USER LOGIN
# =========================
@app.post("/user/login")
def user_login(
    account_id: int = Form(...),
    login_password: str = Form(...)
):
    cursor.execute(
        """
        SELECT *
        FROM bank
        WHERE account_id = %s
        AND login_password = %s
        """,
        (account_id, login_password)
    )

    account = cursor.fetchone()

    if account:
        return RedirectResponse(
            url=f"/user/dashboard/{account_id}",
            status_code=303
        )

    return RedirectResponse(
        url="/user/login",
        status_code=303
    )


# =========================
# USER DASHBOARD
# =========================
@app.get("/user/dashboard/{account_id}")
def user_dashboard(request: Request, account_id: int):

    cursor.execute(
        """
        SELECT *
        FROM bank
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if not account:
        return RedirectResponse(
            url="/user/login",
            status_code=303
        )

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE account_id = %s
        ORDER BY transaction_time DESC
        """,
        (account_id,)
    )

    transactions = cursor.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="user_dashboard.html",
        context={
            "account": account,
            "transactions": transactions
        }
    )


# =========================
# DEPOSIT
# =========================
@app.post("/user/deposit")
def deposit(
    account_id: int = Form(...),
    amount: float = Form(...)
):

    if amount <= 0:
        return RedirectResponse(
            url=f"/user/dashboard/{account_id}",
            status_code=303
        )

    cursor.execute(
        """
        SELECT account_id
        FROM bank
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account:

        cursor.execute(
            """
            UPDATE bank
            SET balance = balance + %s,
                transaction_time = CURRENT_TIMESTAMP
            WHERE account_id = %s
            """,
            (amount, account_id)
        )

        cursor.execute(
            """
            INSERT INTO transactions
            (account_id, type, amount)
            VALUES (%s, %s, %s)
            """,
            (account_id, "Deposit", amount)
        )

        conn.commit()

    return RedirectResponse(
        url=f"/user/dashboard/{account_id}",
        status_code=303
    )


# =========================
# WITHDRAW
# =========================
@app.post("/user/withdraw")
def withdraw(
    account_id: int = Form(...),
    amount: float = Form(...)
):

    if amount <= 0:
        return RedirectResponse(
            url=f"/user/dashboard/{account_id}",
            status_code=303
        )

    cursor.execute(
        """
        SELECT balance
        FROM bank
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account:

        current_balance = float(account["balance"])

        if current_balance >= amount:

            cursor.execute(
                """
                UPDATE bank
                SET balance = balance - %s,
                    transaction_time = CURRENT_TIMESTAMP
                WHERE account_id = %s
                """,
                (amount, account_id)
            )

            cursor.execute(
                """
                INSERT INTO transactions
                (account_id, type, amount)
                VALUES (%s, %s, %s)
                """,
                (account_id, "Withdraw", amount)
            )

            conn.commit()

    return RedirectResponse(
        url=f"/user/dashboard/{account_id}",
        status_code=303
    )


# =========================
# ADMIN LOGIN PAGE
# =========================
@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={}
    )


# =========================
# ADMIN LOGIN
# =========================
@app.post("/admin/login")
def admin_login(
    username: str = Form(...),
    password: str = Form(...)
):

    if username == "admin" and password == "admin123":

        return RedirectResponse(
            url="/admin/dashboard",
            status_code=303
        )

    return RedirectResponse(
        url="/admin/login",
        status_code=303
    )


# =========================
# ADMIN DASHBOARD
# =========================
@app.get("/admin/dashboard")
def admin_dashboard(request: Request):

    # All accounts
    cursor.execute(
        """
        SELECT *
        FROM bank
        ORDER BY account_id DESC
        """
    )

    accounts = cursor.fetchall()


    # All transactions
    cursor.execute(
        """
        SELECT
            t.transaction_id,
            t.account_id,
            b.name,
            t.type,
            t.amount,
            t.transaction_time
        FROM transactions t
        JOIN bank b
        ON t.account_id = b.account_id
        ORDER BY t.transaction_time DESC
        """
    )

    transactions = cursor.fetchall()


    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "accounts": accounts,
            "transactions": transactions
        }
    )


# =========================
# CREATE ACCOUNT
# =========================
@app.post("/admin/create")
def create_account(
    name: str = Form(...),
    login_password: str = Form(...),
    balance: float = Form(...)
):

    if balance < 0:
        return RedirectResponse(
            url="/admin/dashboard",
            status_code=303
        )

    cursor.execute(
        """
        INSERT INTO bank
        (name, login_password, balance)
        VALUES (%s, %s, %s)
        """,
        (name, login_password, balance)
    )

    conn.commit()

    return RedirectResponse(
        url="/admin/dashboard",
        status_code=303
    )


# =========================
# DELETE ACCOUNT
# =========================
@app.post("/admin/delete")
def delete_account(account_id: int = Form(...)):

    cursor.execute(
        """
        DELETE FROM transactions
        WHERE account_id = %s
        """,
        (account_id,)
    )

    cursor.execute(
        """
        DELETE FROM bank
        WHERE account_id = %s
        """,
        (account_id,)
    )

    conn.commit()

    return RedirectResponse(
        url="/admin/dashboard",
        status_code=303
    )


# =========================
# LOGOUT
# =========================
@app.get("/logout")
def logout():

    return RedirectResponse(
        url="/",
        status_code=303
    )
