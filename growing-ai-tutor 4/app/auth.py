from fastapi import HTTPException, Request, status


def require_login(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
