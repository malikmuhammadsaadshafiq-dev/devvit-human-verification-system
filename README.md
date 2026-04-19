# Devvit Human Verification System

A comprehensive Reddit community verification system that automatically validates human participation through multi-factor checks and provides real-time user flair updates based on verification status.

## Problem Solved

Subreddit moderation teams face significant challenges in maintaining authentic community participation. Traditional verification methods are manual, time-consuming, and prone to errors. This system solves:

- **Bot infiltration** in subreddit communities
- **Manual verification overhead** for moderators
- **Delayed user onboarding** due to slow verification
- **Inconsistent verification standards** across different communities

## Architecture Overview

```svg
<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="blueGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1e40af;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="greenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#22c55e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#16a34a;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Reddit Platform -->
  <rect x="50" y="50" width="120" height="60" rx="8" fill="#ff4500" />
  <text x="110" y="85" text-anchor="middle" fill="white" font-family="system-ui" font-size="14" font-weight="600">Reddit</text>
  
  <!-- Devvit App -->
  <rect x="50" y="150" width="120" height="60" rx="8" fill="url(#blueGradient)" />
  <text x="110" y="185" text-anchor="middle" fill="white" font-family="system-ui" font-size="14">Devvit App</text>
  
  <!-- API Layer -->
  <rect x="250" y="150" width="120" height="60" rx="8" fill="url(#blueGradient)" />
  <text x="310" y="185" text-anchor="middle" fill="white" font-family="system-ui" font-size="14">FastAPI</text>
  
  <!-- Database -->
  <rect x="450" y="150" width="120" height="60" rx="8" fill="#64748b" />
  <text x="510" y="185" text-anchor="middle" fill="white" font-family="system-ui" font-size="14">PostgreSQL</text>
  
  <!-- Next.js Frontend -->
  <rect x="650" y="150" width="120" height="60" rx="8" fill="url(#blueGradient)" />
  <text x="710" y="185" text-anchor="middle" fill="white" font-family="system-ui" font-size="14">Next.js</text>
  
  <!-- Kafka/Queue -->
  <rect x="250" y="250" width="120" height="60" rx="8" fill="#8b5cf6" />
  <text x="310" y="285" text-anchor="middle" fill="white" font-family="system-ui" font-size="14">Queue</text>
  
  <!-- Redis Cache -->
  <rect x="450" y="250" width="120" height="60" rx="8" fill="#f59e0b" />
  <text x="510" y="285" text-anchor="middle" fill="white" font-family="system-ui" font-size="14">Redis</text>
  
  <!-- Reddit Users -->
  <ellipse cx="110" cy="400" rx="50" ry="40" fill="url(#greenGradient)" opacity="0.8" />
  <text x="110" y="405" text-anchor="middle" fill="white" font-family="system-ui" font-size="12">Reddit Users</text>
  
  <!-- Moderators -->
  <ellipse cx="310" cy="400" rx="50" ry="40" fill="url(#greenGradient)" opacity="0.8" />
  <text x="310" y="405" text-anchor="middle" fill="white" font-family="system-ui" font-size="12">Moderators</text>
  
  <!-- Connections -->
  <line x1="110" y1="110" x2="110" y2="150" stroke="#94a3b8" stroke-width="2" />
  <line x1="110" y1="210" x2="250" y2="180" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrowhead)" />
  <line x1="370" y1="180" x2="450" y2="180" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrowhead)" />
  <line x1="630" y1="180" x2="650" y2="180" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrowhead)" />
  <line x1="310" y1="210" x2="310" y2="250" stroke="#94a3b8" stroke-width="2" />
  <line x1="370" y1="280" x2="450" y2="280" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrowhead)" />
  <line x1="110" y1="440" x2="110" y2="400" stroke="#94a3b8" stroke-width="2" />
  <line x1="310" y1="440" x2="310" y2="400" stroke="#94a3b8" stroke-width="2" />
  
  <!-- Arrows -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
    </marker>
  </defs>
  
  <!-- Process Boxes -->
  <rect x="50" y="480" width="140" height="40" rx="20" fill="#e2e8f0" stroke="#94a3b8" />
  <text x="120" y="505" text-anchor="middle" fill="#475569" font-family="system-ui" font-size="12">Post Analysis</text>
  
  <rect x="250" y="480" width="140" height="40" rx="20" fill="#e2e8f0" stroke="#94a3b8" />
  <text x="320" y="505" text-anchor="middle" fill="#475569" font-family="system-ui" font-size="12">Verification Flow</text>
  
  <rect x="450" y="480" width="140" height="40" rx="20" fill="#e2e8f0" stroke="#94a3b8" />
  <text x="520" y="505" text-anchor="middle" fill="#475569" font-family="system-ui" font-size="12">Flair Updates</text>
</svg>
```

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), SQLAlchemy ORM
- **Database**: PostgreSQL with Redis caching
- **API**: RESTful endpoints with real-time webhook support
- **Deployment**: Vercel (frontend), Railway/Render (API)

## Features

### Core Verification
- **Automated post/comment analysis** using ML-based spam detection
- **Behavioral pattern analysis** for account authenticity
- **Multi-factor verification** combining post history, comments, and karma
- **Real-time verification** with instant flair updates

### Moderator Dashboard
- **Community-specific configuration** for verification thresholds
- **Bulk user management** with verification batch processing
- **Analytics and reporting** showing verification success rates
- **Manual override** capabilities for special cases

### User Experience
- **Non-intrusive verification** triggered automatically
- **Clear status communication** via Reddit message system
- **Progress tracking** with helpful verification checkpoints
- **Appeal process** for users flagged incorrectly

### System Security
- **Rate limiting** per user and community
- **Anti-gaming** mechanisms to prevent system abuse
- **Webhook security** with secret signing
- **Audit logging** for all verification decisions

## Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL 13+
- Reddit app with moderator permissions
- Redis server

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/your-org/devvit-verification-system.git
cd devvit-verification-system
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
cd api
pip install -r requirements.txt
```

4. **Environment setup**
```bash
# Frontend .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEST_PUBLIC_DEVVIT_WEBHOOK_SECRET=your_webhook_secret

# Backend .env
DATABASE_URL=postgresql://user:password@localhost:5432/devvit_verification
REDIS_URL=redis://localhost:6379
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
WEBHOOK_SECRET=your_webhook_secret
```

5. **Database setup**
```bash
# Run migrations (in api/ directory)
python -m alembic upgrade head
```

6. **Start development servers**
```bash
# Terminal 1: Backend
cd api && uvicorn index:app --reload --port 8000

# Terminal 2: Frontend
npm run dev
```

## API Documentation

### Authentication
All endpoints require proper authentication headers when called from moderator interfaces.

### Core Endpoints

#### Verification Flow
```
POST /api/v1/verification/start
{
  "user_id": "reddit_username",
  "subreddit": "subreddit_name",
  "trigger": "post|comment_request"
}

GET /api/v1/verification/status/{user_id}/{subreddit}
- Returns current verification status

POST /api/v1/verification/complete
{
  "user_id": "reddit_username",
  "subreddit": "subreddit_name",
  "verification_score": 0.87
}
```

#### Admin/Moderator Endpoints
```
GET /api/v1/admin/dashboard/{subreddit}
- Returns community stats and pending verifications

POST /api/v1/admin/configure
{
  "subreddit": "subreddit_name",
  "verification_threshold": 0.75,
  "min_posts": 10,
  "min_comments": 50,
  "karma_threshold": 100
}

PUT /api/v1/admin/bulk-verify
{
  "user_ids": ["user1", "user2"],
  "subreddit": "subreddit_name",
  "action": "approve|deny"
}
```

#### Webhook Endpoints
```
POST /api/v1/webhooks/reddit
- Processes Reddit webhook events
- Validates webhook signature
- Triggers verification flows

POST /api/v1/webhooks/verification-complete
- Updates user flair via Reddit API
- Sends verification complete message
```

## Testing

### Running Tests
```bash
# Backend tests
cd api
python -m pytest tests/ -v

# Frontend component tests
npm run test

# Integration tests
npm run test:e2e
```

### Test Coverage
- Unit tests for all API endpoints
- Component testing for React components
- Integration tests for webhook processing
- End-to-end tests for verification flow

## Screenshots

*[Screenshots will be added after Vercel deployment]*

1. **Moderator Dashboard** - Real-time overview of verification queue
2. **User Verification Modal** - Clean interface for verification process
3. **Configuration Panel** - Subreddit-specific settings management
4. **Analytics Overview** - Performance metrics and success rates

## Deployment

### Production Setup

1. **Vercel Deployment**
```bash
# Deploy frontend
vercel --prod

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NELL_PUBLIC_DEVVIT_WEBHOOK_SECRET=production_webhook_secret
```

2. **Production API**
```bash
# Deploy to Railway/Render
railway up --detach

# Production environment variables
DATABASE_URL=production_postgresql_url
REDIS_URL=production_redis_url
REDDIT_CLIENT_ID=production_reddit_app
WEBHOOK_SECRET=production_webhook_secret
```

### Environment Variables
- `REDDIT_CLIENT_ID`: App ID from Reddit console
- `REDDIT_CLIENT_SECRET`: Reddit app secret
- `WEBHOOK_SECRET`: Secure random string for webhook validation
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/awesome-feature`
3. Commit changes: `git commit -m 'Add awesome feature'`
4. Push to branch: `git push origin feature/awesome-feature`
5. Open a Pull Request

## Security Considerations

- **Webhook validation** using HMAC signatures
- **Rate limiting** per IP and user
- **Input validation** on all API endpoints
- **SQL injection prevention** via SQLAlchemy ORM
- **Cross-site scripting** protection in frontend

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For questions or support:
- Create an issue in this repository
- Join our Discord community
- Email: support@devvit-verification.com