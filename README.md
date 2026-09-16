# F1 Predictor 2026 🏎️

> AI-Powered Formula 1 Race Predictions for the 2026 Season

## 🔐 Authentication Required

**All access to the platform now requires user authentication.** You must login or signup before using any features.

### Quick Start with Auth

```bash
# 1. Run the quickstart script (creates .env, installs deps, starts servers)
./quickstart.sh

# 2. Open browser and login
# Default admin credentials (CHANGE THESE!):
# Email: admin@f1predictor.com
# Password: F1Admin2026!Secure
```

See [AUTH_SETUP.md](AUTH_SETUP.md) for detailed setup instructions.

---

## Features

- 🎯 **Monte Carlo Simulations** - 100-50,000 race simulations
- 📊 **Real-time Predictions** - Race, qualifying, practice forecasts
- 👥 **Head-to-Head Analysis** - Driver vs driver comparisons
- 🏆 **Live Standings** - Driver and constructor championships
- 🎮 **Fantasy League** - Build your dream team
- 📰 **AI News Integration** - Latest F1 news with AI insights
- 📈 **Analytics Dashboard** - Model accuracy and performance metrics
- 🔒 **Secure Authentication** - JWT-based auth with bcrypt passwords

## Tech Stack

**Backend:**
- FastAPI (Python)
- SQLite/PostgreSQL
- Redis caching
- JWT authentication
- Monte Carlo engine

**Frontend:**
- React 18 + TypeScript
- TanStack Query
- Chart.js
- Tailwind CSS
- Vite

## Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Clone repository
git clone <repo-url>
cd FORMULA_1_PREDICTOR_2026

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY, ADMIN_PASSWORD

# Start backend
python3 backend/main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Quick Start (Recommended)

```bash
# One-command setup and start
./quickstart.sh
```

## Usage

### 1. Access the Application

Open your browser to `http://localhost:5178`

### 2. Login or Signup

You'll be redirected to the login page. Options:

**Login with Admin Account:**
- Email: `admin@f1predictor.com`
- Username: `admin`
- Password: Your configured `ADMIN_PASSWORD`

**Create New Account:**
- Click "Sign up" on login page
- Fill in registration form
- Start using immediately

### 3. Explore Features

Once logged in, access all features:
- 🏁 **Dashboard** - Race predictions
- 📊 **Standings** - Championship tables
- ⚔️ **H2H** - Driver comparisons
- 🎮 **Fantasy** - Team management
- 📰 **Analytics & News** - Model insights
- ⚙️ **Settings** - Personalization

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

### Authentication Endpoints

```bash
# Register new user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"johndoe","password":"securepass123"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username":"johndoe","password":"securepass123"}'

# Access protected route
curl http://localhost:5000/api/v1/races \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

See all auth endpoints in [AUTH_SETUP.md](AUTH_SETUP.md).

## Testing

### Run Auth Tests

```bash
python3 test_auth.py
```

Tests registration, login, profile retrieval, and protected route access.

### Run Full Test Suite

```bash
cd backend
pytest app/tests/
```

## Configuration

Key environment variables in `.env`:

```env
# Authentication
SECRET_KEY=your-secret-key-here
ADMIN_EMAIL=admin@f1predictor.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
JWT_EXPIRATION_HOURS=24

# Database
DATABASE_URL=sqlite:///./f1_predictions.db

# Frontend
VITE_API_BASE=http://localhost:5000
FRONTEND_ORIGIN=http://localhost:5178
```

Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Security

✅ **Password Security**
- Bcrypt hashing (work factor 12)
- Minimum 8 characters
- Never stored in plaintext

✅ **JWT Tokens**
- Access token: 24-hour expiry
- Refresh token: 7-day expiry
- HS256 signing algorithm

✅ **Route Protection**
- All API routes require authentication
- Automatic token validation
- Admin privilege support

⚠️ **Production Checklist**
- [ ] Change SECRET_KEY
- [ ] Change ADMIN_PASSWORD
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up monitoring
- [ ] Enable rate limiting

## Project Structure

```
FORMULA_1_PREDICTOR_2026/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   └── auth.py          # Auth endpoints
│   │   ├── services/
│   │   │   └── auth_service.py  # Auth logic
│   │   ├── security/
│   │   │   └── auth_middleware.py
│   │   ├── database/
│   │   │   └── models.py        # User models
│   │   └── __init__.py
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── auth.ts          # Auth API client
│   │   ├── context/
│   │   │   └── AuthContext.tsx  # React auth state
│   │   ├── components/auth/
│   │   │   └── ProtectedRoute.tsx
│   │   ├── pages/
│   │   │   ├── Login/
│   │   │   └── Signup/
│   │   └── app/
│   │       ├── router.tsx       # Route protection
│   │       └── providers.tsx    # AuthProvider
│   └── package.json
├── AUTH_SETUP.md                # Detailed auth guide
├── AUTH_IMPLEMENTATION_SUMMARY.md
├── test_auth.py                 # Auth tests
└── quickstart.sh                # Easy setup script
```

## Documentation

- **[AUTH_SETUP.md](AUTH_SETUP.md)** - Complete authentication setup guide
- **[AUTH_IMPLEMENTATION_SUMMARY.md](AUTH_IMPLEMENTATION_SUMMARY.md)** - Implementation details
- **[FIXES_SUMMARY.md](FIXES_SUMMARY.md)** - Recent bug fixes
- **API Docs** - `http://localhost:5000/docs`

## Troubleshooting

### "Authentication required" error
- Ensure you're logged in
- Check token: `localStorage.getItem('f1_access_token')`
- Try logging out and back in

### "Invalid credentials" error
- Verify email/username and password
- Check if admin user was created
- Review backend logs: `tail -f /tmp/f1_backend.log`

### Backend won't start
- Check dependencies: `pip install -e ".[dev]"`
- Verify .env file exists
- Check port 5000 is free

### Frontend won't load
- Ensure backend is running
- Check `VITE_API_BASE` in .env
- Clear browser cache

See [AUTH_SETUP.md](AUTH_SETUP.md) for more troubleshooting tips.

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

MIT License - see LICENSE file

## Support

- 📖 Read [AUTH_SETUP.md](AUTH_SETUP.md)
- 🐛 Run `test_auth.py` for diagnostics
- 📝 Check backend logs: `/tmp/f1_backend.log`
- 💬 Open an issue on GitHub

---

**Built with ❤️ for F1 fans**  
**Version:** 1.0.0  
**Last Updated:** 2026-09-16
