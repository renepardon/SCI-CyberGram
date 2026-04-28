from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def feed(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    posts = conn.execute("""
        SELECT posts.*, users.username, users.profile_pic
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """).fetchall()
    conn.close()

    return templates.TemplateResponse("feed.html", {
        "request": request,
        "user": user,
        "posts": posts,
    })
