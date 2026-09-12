# Auth Parity Fix
Active predictions blueprint previously did not require auth while dormant dashboard.py used require_auth.
Resolution: v1 endpoints accept anonymous by default but validate JWT if Authorization: Bearer <token> present via security/auth.decode_jwt_token. Future hardening can enforce require_auth on selected routes without breaking dashboard (which never sent a token). This reconciles inconsistency without forcing anonymous dashboard to authenticate.
