### CyberGram Security Analysis

This document provides answers to the security mission described in `README.md`, identifying the vulnerabilities, how to reproduce them, and recommended fixes.

---

### 1. Can you log in without knowing a password?
- **Vulnerability Name:** SQL Injection (SQLi)
- **Location:** `routes/auth.py` in the `login` function.
- **Reproduce:** 
  1. Go to the login page.
  2. Enter `admin' --` in the username field.
  3. Enter any text in the password field.
  4. The resulting query becomes `SELECT * FROM users WHERE username = 'admin' --' AND password = '...'`, which logs you in as `admin`.
- **Fix:** Use parameterized queries instead of f-strings.
  ```python
  conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
  ```

### 2. Can you make something unexpected appear on other users' screens?
- **Vulnerability Name:** Stored Cross-Site Scripting (XSS)
- **Location:** `templates/post.html` and `templates/profile.html` use the `| safe` filter on user-generated content (captions, comments, bio).
- **Reproduce:**
  1. Log in and go to a post.
  2. Post a comment like: `<script>alert('Hacked!')</script>` or `<img src=x onerror=alert(1)>`.
  3. Anyone viewing that post will execute the script.
- **Fix:** Remove the `| safe` filter from Jinja2 templates to allow automatic HTML escaping.
  ```html
  <span>{{ comment['content'] }}</span>
  ```

### 3. Can you edit someone else's profile or delete their post?
- **Vulnerability Name:** Insecure Direct Object Reference (IDOR)
- **Location:** `routes/profile.py` (`edit_profile`) and `routes/post.py` (`delete_post`).
- **Reproduce:**
  1. Log in as any user.
  2. To delete a post: Send a POST request to `/post/<target_post_id>/delete` (e.g., via Intercepting Proxy or a crafted form).
  3. To edit a profile: Go to `/profile/edit/<target_user_id>` and submit the form.
- **Fix:** Verify that the `current_user['id']` matches the owner of the resource before performing the action.
  ```python
  post = conn.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
  if post['user_id'] != user['id']:
      return Forbidden()
  ```

### 4. Can you become another user without logging in as them?
- **Vulnerability Name:** Broken Authentication / Session Hijacking (Insecure Cookie)
- **Location:** `routes/auth.py` in `login` and `get_current_user`.
- **Reproduce:**
  1. Look at your cookies in the browser developer tools.
  2. Notice the `user_id` cookie is a plaintext integer (e.g., `2` for Alice).
  3. Change the cookie value to `1` and refresh the page to become the `admin`.
- **Fix:** Use signed session cookies (like `SessionMiddleware` in FastAPI/Starlette) and set `httpOnly` and `Secure` flags.

### 5. Can you upload something that isn't an image?
- **Vulnerability Name:** Unrestricted File Upload
- **Location:** `routes/profile.py` and `routes/post.py`.
- **Reproduce:**
  1. Go to "New Post" or "Edit Profile".
  2. Upload a `.html` file containing a script or a `.php` file (if the server supported it).
  3. Access the file via `/uploads/...`.
- **Fix:** Validate the file extension and MIME type against an allow-list (e.g., `image/jpeg`, `image/png`). Rename uploaded files to random strings.

### 6. Can you read files from the server that you shouldn't have access to?
- **Vulnerability Name:** Local File Inclusion (LFI) / Path Traversal
- **Location:** `routes/profile.py` in the `serve_file` function.
- **Reproduce:**
  1. Navigate to `http://localhost:8000/file/../../etc/passwd`.
  2. The server will join `uploads` with `../../etc/passwd` and return the system file.
- **Fix:** Sanitize the file path using `os.path.basename()` or use FastAPI's `StaticFiles` which handles this securely, rather than a manual route.
- **Exploit:** ``curl --path-as-is http://localhost:8000/file/../../etc/passwd``

### 7. Can you trick a logged-in user into performing actions they didn't intend?
- **Vulnerability Name:** Cross-Site Request Forgery (CSRF)
- **Location:** All POST routes (`/post/new`, `/post/{id}/comment`, `/post/{id}/delete`, `/profile/edit/{id}`).
- **Reproduce:**
  1. Create a malicious HTML page on a different domain with a hidden form that POSTs to `http://localhost:8000/post/1/delete`.
  2. Trick the logged-in admin into clicking a link to your page.
  3. The browser will automatically send the `user_id` cookie, and the post will be deleted.
- **Fix:** Implement CSRF tokens for all state-changing requests (POST/PUT/DELETE).
