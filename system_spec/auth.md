# Spec: Auth — GitHub OAuth + JWT

## Endpoints

| Metodo | Path | Auth | Descripcion |
|---|---|---|---|
| POST | `/auth/github` | No | Intercambiar code por JWT (uso directo del frontend) |
| GET | `/auth/callback` | No | Callback de GitHub OAuth, redirige al frontend con JWT |

## Flujo OAuth completo

```
1. Frontend redirige a GitHub:
   https://github.com/login/oauth/authorize?client_id=...&redirect_uri=http://localhost:8000/auth/callback&scope=user

2. GitHub redirige al backend:
   GET /auth/callback?code=abc123

3. Backend intercambia code por access_token con GitHub API

4. Backend obtiene perfil del usuario (GET https://api.github.com/user)

5. Backend genera JWT con { sub: user_id, login: username }

6. Backend redirige al frontend:
   http://localhost:4200/login-success?token=JWT_TOKEN

7. Frontend guarda JWT en localStorage
```

## JWT

- Algoritmo: HS256
- Expiracion: 24 horas
- Secret: variable `JWT_SECRET` (fallback a `OPENAI_API_KEY` si no esta definido)
- Payload: `{ sub: str, login: str, exp: datetime }`

## Proteccion de endpoints

Todos los endpoints `/pipeline/*` requieren `Authorization: Bearer <JWT>`.
Se valida con `Depends(get_current_user)` que decodifica el token.

## Schemas

```python
class GitHubAuthRequest(BaseModel):
    code: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict   # { id, login, avatar_url, name }
```

## Archivos involucrados

- `app/routers/auth.py` — endpoints POST /github, GET /callback
- `app/services/auth_service.py` — exchange_code_for_token()
- `app/core/security.py` — create_access_token(), decode_access_token(), get_current_user()
- `app/schemas/auth.py` — GitHubAuthRequest, AuthTokenResponse
