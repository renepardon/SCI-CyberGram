# CyberGram

A deliberately vulnerable social media clone for security testing and learning.

## Getting Started

### Requirements
- [Docker](https://www.docker.com/products/docker-desktop/)

### Run the Lab

```bash
docker run -p 8000:8000 marcothedebugger/cybergram
```

Open **http://localhost:8000** in your browser.

### User Accounts

| Username | Password |
|----------|----------|
| admin | admin123 |
| alice | password |
| bob | bob2024 |

### Reset the Lab

Restart the container to reset everything (database, uploads) back to the default state:

```bash
docker restart <container_id>
```

## Your Mission

This application contains **7 security vulnerabilities**. Find and exploit them.

1. **Can you log in without knowing a password?**
2. **Can you make something unexpected appear on other users' screens?**
3. **Can you edit someone else's profile or delete their post?**
4. **Can you become another user without logging in as them?**
5. **Can you upload something that isn't an image?**
6. **Can you read files from the server that you shouldn't have access to?**
7. **Can you trick a logged-in user into performing actions they didn't intend?**

> **Hint:** Each question maps to a different vulnerability class from the OWASP Top 10.

## Rules

- Only attack **your own local instance**
- Do not use automated scanners — try to find and exploit vulnerabilities manually
- Document each finding with: the vulnerability name, where you found it, how to reproduce it, and how you would fix it
