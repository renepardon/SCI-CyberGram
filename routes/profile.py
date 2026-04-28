import os
import shutil
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile/{username}")
def view_profile(request: Request, username: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    profile_user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if not profile_user:
        conn.close()
        return RedirectResponse(url="/", status_code=302)

    posts = conn.execute(
        "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC",
        (profile_user["id"],),
    ).fetchall()
    conn.close()

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "profile_user": profile_user,
        "posts": posts,
    })


@router.get("/profile/edit/{user_id}")
def edit_profile_page(request: Request, user_id: int):
    """VULN: IDOR - anyone can edit any profile by changing the user_id in the URL."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    # No ownership check - IDOR vulnerability
    profile_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not profile_user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse("profile_edit.html", {
        "request": request,
        "user": user,
        "profile_user": profile_user,
    })


@router.post("/profile/edit/{user_id}")
async def edit_profile(
    request: Request,
    user_id: int,
    bio: str = Form(""),
    profile_pic: UploadFile = File(None),
):
    """VULN: IDOR + Unrestricted File Upload - no ownership check, no file validation."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    pic_path = ""

    if profile_pic and profile_pic.filename:
        # VULN: Unrestricted File Upload - no type/size validation, original filename used
        upload_dir = os.path.join("uploads", "profiles")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, profile_pic.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(profile_pic.file, f)

        pic_path = f"/uploads/profiles/{profile_pic.filename}"
        conn.execute(
            "UPDATE users SET bio = ?, profile_pic = ? WHERE id = ?",
            (bio, pic_path, user_id),
        )
    else:
        conn.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))

    conn.commit()
    conn.close()

    # Redirect back to the edited user's profile
    conn = get_db()
    edited_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    return RedirectResponse(url=f"/profile/{edited_user['username']}", status_code=302)


@router.get("/file/{file_path:path}")
def serve_file(file_path: str):
    """VULN: Path Traversal - no sanitization of file_path, can access arbitrary files."""
    full_path = os.path.join("uploads", file_path)
    return FileResponse(full_path)
