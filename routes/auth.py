from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request):
    """Get user from cookie - intentionally vulnerable: plain user_id cookie, not signed."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    
    # VULN: SQL Injection - user_id comes straight from cookie
    user = conn.execute(f"SELECT * FROM users WHERE id = {user_id}").fetchone()
    conn.close()
    return user


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    # VULN: SQL Injection - raw f-string query with user input
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    user = conn.execute(query).fetchone()
    conn.close()

    if user:
        # VULN: Broken Auth - plain user_id in cookie, no httpOnly, no secure flag
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="user_id", value=str(user["id"]))
        return response

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid username or password",
    })


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("user_id")
    return response
