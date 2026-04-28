# CyberGram - Vulnerability Breakdown

## 1. SQL Injection

**Where:** Login (`routes/auth.py` line 33-34) and comment creation (`routes/post.py` line 93-95)

**How it works:** User input is inserted directly into SQL queries via f-strings instead of parameterized queries.

```python
# auth.py - login
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

An attacker can type `' OR 1=1 --` as the username to bypass authentication entirely. The query becomes:

```sql
SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = '...'
```

The `--` comments out the password check, and `OR 1=1` matches all rows — logging in as the first user (admin).

The comment insertion in `routes/post.py` is similarly injectable, potentially allowing data extraction or modification via `UNION` queries.

---

## 2. Stored XSS (Cross-Site Scripting)

**Where:** Post captions (`templates/feed.html`), comments (`templates/post.html`), and user bios (`templates/profile.html`)

**How it works:** Jinja2 auto-escapes HTML by default, but we use the `| safe` filter to explicitly disable escaping:

```html
{{ post['caption'] | safe }}
{{ comment['content'] | safe }}
{{ profile_user['bio'] | safe }}
```

An attacker can submit `<script>alert(document.cookie)</script>` as a caption, comment, or bio. This script executes in every visitor's browser, enabling cookie theft, session hijacking, or phishing.

---

## 3. IDOR (Insecure Direct Object Reference)

**Where:** Profile editing (`routes/profile.py` line 44-46) and post deletion (`routes/post.py` line 100-112)

**How it works:** The edit profile endpoint uses the `user_id` from the URL with **no ownership check**:

```python
@router.get("/profile/edit/{user_id}")
def edit_profile_page(request: Request, user_id: int):
    # No check that user_id == logged-in user's id
    profile_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
```

Any logged-in user can visit `/profile/edit/1` to edit the admin's profile. Similarly, `POST /post/5/delete` deletes post #5 regardless of who owns it.

---

## 4. Broken Authentication / Weak Cookies

**Where:** Cookie setting (`routes/auth.py` line 38-40) and cookie reading (`routes/auth.py` line 14-19)

**How it works:** The session is a plain `user_id` cookie with no signing, no `httpOnly`, and no `Secure` flag:

```python
response.set_cookie(key="user_id", value=str(user["id"]))  # just "1", "2", etc.
```

An attacker can open browser DevTools, change the cookie value from `user_id=2` to `user_id=1`, and instantly become the admin. Additionally, the cookie is readable by JavaScript (no `httpOnly`), so any XSS attack can steal it via `document.cookie`.

The `get_current_user` function also has a SQL injection in the cookie value:

```python
user = conn.execute(f"SELECT * FROM users WHERE id = {user_id}").fetchone()
```

---

## 5. Unrestricted File Upload

**Where:** Profile picture upload (`routes/profile.py` line 73-79) and post image upload (`routes/post.py` line 39-43)

**How it works:** There is zero validation on uploaded files — no file type check, no size limit, and the original filename is preserved:

```python
file_path = os.path.join(upload_dir, profile_pic.filename)
with open(file_path, "wb") as f:
    shutil.copyfileobj(profile_pic.file, f)
```

An attacker can upload a `.html` file containing JavaScript (stored XSS via file), a web shell, or any malicious binary. The file is then served directly at a predictable URL like `/uploads/profiles/malware.html`.

---

## 6. Path Traversal

**Where:** File serving route (`routes/profile.py` line 99-102)

**How it works:** The `/file/{file_path}` endpoint joins user input directly into a file path with no sanitization:

```python
@router.get("/file/{file_path:path}")
def serve_file(file_path: str):
    full_path = os.path.join("uploads", file_path)
    return FileResponse(full_path)
```

An attacker can request `/file/../../etc/passwd` which resolves to `uploads/../../etc/passwd` → `/etc/passwd`, reading arbitrary files from the server filesystem.

---

## 7. CSRF (Cross-Site Request Forgery)

**Where:** Every form in the application — login, profile edit, post creation, comment submission, post deletion.

**How it works:** None of the forms include a CSRF token. An attacker can create a malicious page on another domain:

```html
<form method="POST" action="http://localhost:8000/post/1/delete">
    <button>Click here for a prize!</button>
</form>
```

If a logged-in CyberGram user visits this page and clicks the button, their browser sends the request **with their cookies attached**, deleting post #1 without their knowledge. This works because the server has no way to verify the request originated from its own forms.

---

## Vulnerability Chain Example

These vulnerabilities can be combined for maximum impact:

1. **SQLi** at login → gain admin access
2. **Stored XSS** in bio → inject `<script>` that steals other users' cookies via `document.cookie`
3. **Broken Auth** → use stolen cookie to impersonate victims
4. **IDOR** → edit victims' profiles or delete their posts
5. **Unrestricted Upload** → upload a web shell for server-side access
6. **Path Traversal** → read server config, source code, or secrets

---

## Key Takeaways

- Think like an attacker, report like a defender.
- Every input is attacker-controlled until proven otherwise.
- One confirmed proof-of-concept beats ten theoretical guesses.
- Document and move on — breadth matters as much as depth.
- A finding without reproducible steps is not a finding.
- Severity is defined by impact, not by how clever the exploit is.
- Always look for chains — single vulnerabilities rarely tell the full story.
- Stay in scope. Always.
