import os
import shutil
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/post/new")
def new_post_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("post_new.html", {
        "request": request,
        "user": user,
    })


@router.post("/post/new")
async def create_post(
    request: Request,
    caption: str = Form(""),
    image: UploadFile = File(...),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # VULN: Unrestricted File Upload - no type/size check
    upload_dir = os.path.join("uploads", "posts")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, image.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    image_url = f"/uploads/posts/{image.filename}"

    conn = get_db()
    conn.execute(
        "INSERT INTO posts (user_id, image, caption) VALUES (?, ?, ?)",
        (user["id"], image_url, caption),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/", status_code=302)


@router.get("/post/{post_id}")
def view_post(request: Request, post_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    post = conn.execute("""
        SELECT posts.*, users.username, users.profile_pic
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.id = ?
    """, (post_id,)).fetchone()

    if not post:
        conn.close()
        return RedirectResponse(url="/", status_code=302)

    comments = conn.execute("""
        SELECT comments.*, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.post_id = ?
        ORDER BY comments.created_at ASC
    """, (post_id,)).fetchall()
    conn.close()

    return templates.TemplateResponse("post.html", {
        "request": request,
        "user": user,
        "post": post,
        "comments": comments,
    })


@router.post("/post/{post_id}/comment")
def add_comment(request: Request, post_id: int, content: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    # VULN: SQL Injection - raw f-string with user input
    conn.execute(
        f"INSERT INTO comments (post_id, user_id, content) VALUES ({post_id}, {user['id']}, '{content}')"
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/post/{post_id}", status_code=302)


@router.post("/post/{post_id}/delete")
def delete_post(request: Request, post_id: int):
    """VULN: IDOR - no ownership check, any logged-in user can delete any post."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/", status_code=302)
