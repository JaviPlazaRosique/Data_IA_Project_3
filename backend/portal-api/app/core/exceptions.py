from fastapi import HTTPException, status

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se han podido validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)

email_taken_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Ese email ya está registrado",
)

username_taken_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Ese nombre de usuario ya está en uso",
)

invalid_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email o contraseña incorrectos",
    headers={"WWW-Authenticate": "Bearer"},
)

inactive_user_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Cuenta de usuario inactiva",
)
