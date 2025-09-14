# Complete Tutorial: Migrating Flask NoteTaking App to Vercel with Supabase


## Table of Contents
1. [Overview](#overview)
2. [Stage 1: Refactor App to Use Supabase](#stage-1-refactor-app-to-use-supabase)
3. [Stage 2: Deploy to Vercel](#stage-2-deploy-to-vercel)
4. [Troubleshooting](#troubleshooting)
5. [Best Practices](#best-practices)

## Overview

This guide walks you through migrating your Flask NoteTaking app from SQLite to Supabase, then deploying it to Vercel for global, serverless hosting. The process is split into two clear stages:

- **Stage 1:** Refactor your app to use Supabase as the backend database (PostgreSQL)
- **Stage 2:** Deploy your refactored app to Vercel for scalable, serverless hosting

You will achieve:
- ✅ Migration from SQLite to Supabase PostgreSQL
- ✅ Deployment to Vercel (serverless)
- ✅ Secure, scalable, production-ready architecture

## Understanding the Current Architecture

### Current Setup
Your application currently uses:
- **Flask**: Python web framework running locally
- **SQLite**: Local file-based database (`database/app.db`)
- **SQLAlchemy**: Object-Relational Mapping (ORM) for database operations
- **Local Storage**: Everything runs on your local machine

### Current Database Schema
Your app has two main models:
```python
# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Note Model  
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text, nullable=True)  # JSON list
    event_date = db.Column(db.String(20), nullable=True)
    event_time = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Understanding Vercel

**Vercel** is a cloud platform for deploying modern web applications, especially optimized for:
- **Serverless Functions**: Your Flask app will run as serverless functions
- **Global CDN**: Fast content delivery worldwide  
- **Automatic HTTPS**: Built-in SSL certificates
- **Git Integration**: Deploy automatically on code pushes
- **Zero Configuration**: Minimal setup required

### Key Concepts:
- **Serverless Functions**: Code runs on-demand without managing servers
- **Cold Starts**: Functions may take extra time on first request
- **Request Limits**: Maximum execution time per request (typically 10-60 seconds)
- **Stateless**: No persistent storage between requests

## Understanding Supabase

**Supabase** is an open-source Firebase alternative that provides:
- **PostgreSQL Database**: Full-featured relational database
- **Real-time subscriptions**: Live updates across clients
- **Built-in Authentication**: User management system
- **API Auto-generation**: REST and GraphQL APIs from your schema
- **Dashboard**: Web interface for database management

### Key Benefits:
- **Managed Database**: No server maintenance required
- **Global Availability**: Multiple regions for low latency
- **Automatic Backups**: Built-in data protection
- **Scaling**: Handles traffic spikes automatically
- **SQL Compatibility**: Full PostgreSQL features

## Migration Strategy

### Phase 1: Database Migration
1. Create Supabase project
2. Set up PostgreSQL database
3. Create tables matching current SQLite schema
4. Update connection strings

### Phase 2: Application Refactoring
1. Update database configuration for PostgreSQL
2. Modify Flask app structure for Vercel
3. Update dependencies
4. Configure environment variables

### Phase 3: Deployment
1. Configure Vercel settings
2. Deploy to Vercel
3. Test all functionality
4. Set up monitoring

## Step 1: Setting up Supabase

### 1.1 Create Supabase Account and Project

1. **Visit Supabase**: Go to [https://supabase.com](https://supabase.com)
2. **Sign Up**: Create account using GitHub, Google, or email
3. **Create New Project**:
   - Click "New Project"
   - Organization: Select or create one
   - Project Name: `notetaking-app`
   - Database Password: Generate a strong password (save this!)
   - Region: Choose closest to your users
   - Pricing Plan: Start with "Free" tier

### 1.2 Get Database Connection Details

Once your project is created (takes ~2 minutes):

1. **Go to Project Settings**:
   - Click the gear icon (⚙️) in the sidebar
   - Navigate to "Database" section

2. **Note Down Connection Details**:
   ```
   Host: db.[project-ref].supabase.co
   Database name: postgres
   Port: 5432
   User: postgres
   Password: [your-database-password]
   ```

3. **Get Connection String**:
   ```
   postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   ```

### 1.3 Configure Database Access

1. **API Settings**: Go to "API" section in settings
2. **Note Down**:
   - Project URL: `https://[project-ref].supabase.co`
   - API Key (anon public): For client-side access
   - API Key (service_role): For server-side access (keep secret!)

## Step 2: Database Schema Migration

### 2.1 Connect to Supabase Database

You can use the Supabase dashboard or connect directly via SQL:

1. **Using Supabase Dashboard**:
   - Go to "Table Editor" in your project
   - Click "New Table"

2. **Using SQL Editor**:
   - Go to "SQL Editor" in your project
   - Run SQL commands directly

### 2.2 Create Database Tables

Create the following SQL schema in Supabase SQL Editor:

```sql
-- Enable UUID extension (optional but recommended)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create notes table
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT, -- JSON array stored as text
    event_date VARCHAR(20), -- YYYY-MM-DD format
    event_time VARCHAR(20), -- HH:MM format
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_notes_title ON notes(title);
CREATE INDEX idx_notes_created_at ON notes(created_at DESC);
CREATE INDEX idx_notes_updated_at ON notes(updated_at DESC);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Create trigger to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables
CREATE TRIGGER update_notes_updated_at 
    BEFORE UPDATE ON notes 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at_column();
```

### 2.3 Verify Table Creation

In the Supabase Table Editor, you should now see:
- `users` table with 5 columns
- `notes` table with 8 columns
- All indexes and triggers applied

## Step 3: Refactoring the Flask App for Vercel

### 3.1 Update Dependencies

Create a new `requirements.txt` file optimized for Vercel:

```txt
Flask==3.1.1
flask-cors==6.0.0
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
openai==1.106.1
SQLAlchemy==2.0.41
Werkzeug==3.1.3
```

**Key Changes Explained**:
- **`psycopg2-binary`**: PostgreSQL adapter for Python (replaces SQLite)
- **`python-dotenv`**: Better environment variable handling (updated version)
- **Removed `blinker`, `click`, etc.**: Not needed for core functionality

### 3.2 Create Vercel Configuration

Create `vercel.json` in your project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHONPATH": "."
  }
}
```

**Configuration Explained**:
- **`builds`**: Tells Vercel how to build your Python app
- **`routes`**: Defines URL routing (API routes and static files)
- **`env`**: Sets Python path for imports

### 3.3 Restructure for Vercel

Create the following directory structure:

```
MyNoteTaking/
├── api/
│   └── index.py          # Main Vercel function entry point
├── src/                  # Keep existing source code
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── llm.py
├── vercel.json
├── requirements.txt
└── .env
```

### 3.4 Create Vercel Entry Point

Create `api/index.py`:

```python
import os
import sys

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.note import note_bp
import logging

# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Enable CORS for all routes
CORS(app, origins=["*"])

# Database configuration for Supabase PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    raise ValueError("DATABASE_URL environment variable is required")

# Configure SQLAlchemy for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {
        'sslmode': 'require'
    }
}

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Route handlers
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and SPA routes"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'database': 'connected'}

# Export for Vercel
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda status, headers: None)

# For local development
if __name__ == '__main__':
    app.run(debug=True)
```

### 3.5 Update Database Models

Update `src/models/user.py` for PostgreSQL compatibility:

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

Update `src/models/note.py` for PostgreSQL compatibility:

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db
import json

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text, nullable=True)  # JSON array stored as text
    event_date = db.Column(db.String(20), nullable=True)  # YYYY-MM-DD
    event_time = db.Column(db.String(20), nullable=True)  # HH:MM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.title}>'

    def get_tags_list(self):
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except Exception:
            # fallback: comma-separated
            return [t.strip() for t in str(self.tags).split(',') if t.strip()]

    def set_tags_list(self, tags_list):
        if not tags_list:
            self.tags = None
        else:
            # ensure list of strings
            self.tags = json.dumps([str(t) for t in tags_list])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.get_tags_list(),
            'event_date': self.event_date,
            'event_time': self.event_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

## Step 4: Environment Configuration

### 4.1 Create Environment Variables File

Create `.env` file in your project root (for local development):

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Flask Configuration
SECRET_KEY=your-super-secret-key-here-change-this-in-production
FLASK_ENV=development

# OpenAI/LLM Configuration
GITHUB_TOKEN=your-github-token-for-llm-api

# Supabase Configuration (optional, for direct API access)
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

**Important**: Replace placeholders with your actual values:
- `[YOUR_PASSWORD]`: Your Supabase database password
- `[PROJECT_REF]`: Your Supabase project reference ID
- `your-github-token-for-llm-api`: Your GitHub token for AI features

### 4.2 Update .gitignore

Ensure your `.gitignore` includes:

```gitignore
# Environment variables
.env
.env.local
.env.production

# Database
*.db
database/

# Vercel
.vercel

# Python
__pycache__/
*.pyc
venv/
```

## Step 5: Deployment to Vercel

### 5.1 Install Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Or using yarn
yarn global add vercel
```

### 5.2 Login to Vercel

```bash
vercel login
```

Follow the prompts to authenticate with your Vercel account.

### 5.3 Deploy Project

From your project directory:

```bash
# First deployment
vercel

# Follow the prompts:
# - Set up and deploy? [Y/n] Y
# - Which scope? [your-username]
# - Link to existing project? [y/N] N
# - Project name: [notetaking-app]
# - In which directory is your code located? ./
```

### 5.4 Configure Environment Variables in Vercel

After deployment, add environment variables:

```bash
# Add database URL
vercel env add DATABASE_URL

# Add secret key
vercel env add SECRET_KEY

# Add GitHub token
vercel env add GITHUB_TOKEN

# Add Supabase keys (if needed)
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_KEY
```

When prompted, enter the values and select:
- Environment: **Production**
- Add to Development/Preview: **Yes** (recommended)

### 5.5 Redeploy with Environment Variables

```bash
# Redeploy to apply environment variables
vercel --prod
```

## Step 6: Testing and Verification

### 6.1 Test Basic Functionality

1. **Access your deployed app**: Visit the URL provided by Vercel
2. **Test note creation**: Create a new note via the UI
3. **Test note editing**: Modify an existing note
4. **Test search**: Search for notes by title/content
5. **Test AI features**: Generate a note using the AI functionality

### 6.2 Test API Endpoints

Use curl or a tool like Postman to test:

```bash
# Test health endpoint
curl https://your-app.vercel.app/health

# Test get all notes
curl https://your-app.vercel.app/api/notes

# Test create note
curl -X POST https://your-app.vercel.app/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Note","content":"This is a test note"}'
```

### 6.3 Monitor Logs

Check Vercel logs for any issues:

```bash
# View real-time logs
vercel logs
```

Or view logs in the Vercel dashboard:
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click "Functions" tab to see serverless function logs

## Step 7: Database Schema Synchronization

### 7.1 Create Schema Sync Script

Create `scripts/sync_schema.py`:

```python
"""
Script to synchronize database schema with Supabase
This ensures your local SQLAlchemy models match the Supabase database
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user import db, User
from src.models.note import Note
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'sslmode': 'require'}
    }
    
    db.init_app(app)
    return app

def sync_schema():
    """Synchronize database schema"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database schema synchronized successfully")
            
            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables in database: {tables}")
            
            # Check specific tables
            required_tables = ['users', 'notes']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
                    
        except Exception as e:
            print(f"❌ Error synchronizing schema: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = sync_schema()
    exit(0 if success else 1)
```

### 7.2 Run Schema Sync

```bash
# Make the script executable
chmod +x scripts/sync_schema.py

# Run schema synchronization
python scripts/sync_schema.py
```

### 7.3 Set up Automatic Schema Sync

Add to your deployment workflow by creating `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Sync database schema
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python scripts/sync_schema.py
        
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

### 7.4 Alternative: Update schema via a local script (API-friendly)

If you prefer not to create tables manually in the Supabase dashboard, you can run a local script that applies your SQL schema to Supabase programmatically. This keeps all changes in code and makes schema updates repeatable.

Two safe, local options are provided below:

- Option A (recommended): connect directly to the Supabase PostgreSQL database using the provided `DATABASE_URL` (service role or postgres user) and execute a `schema.sql` file. This uses the standard PostgreSQL wire protocol (psycopg2) and runs locally — it is not a Vercel function.
- Option B (advanced): call a small, one-time-created stored function (`run_sql`) via the PostgREST RPC endpoint (`/rest/v1/rpc/run_sql`) using your Supabase `service_role` key. This lets you POST SQL to an HTTP endpoint. It requires creating the stored function once from the Supabase SQL editor.

Important security notes:

- Use your Supabase `service_role` key only in trusted, local scripts or CI workflows. Never expose it to client-side code.
- Always run these scripts from your local machine or CI (not from Vercel serverless functions, per your requirement).

Option A — Python script: run SQL over a direct DB connection

1. Create a `scripts/schema.sql` file with your full DDL (the same SQL shown earlier in Step 2.2). Example:

```sql
-- scripts/schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    event_date VARCHAR(20),
    event_time VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- triggers and indexes as needed
```

2. Create `scripts/apply_schema.py` (local script that executes `schema.sql`):

```python
#!/usr/bin/env python3
"""Apply SQL schema to Supabase using direct DB connection (psycopg2).

This script runs locally and connects to the database using DATABASE_URL. It is
safe to run from your workstation or CI (use secrets in CI). It uses sslmode=require.
"""
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = PROJECT_ROOT / 'scripts' / 'schema.sql'

DATABASE_URL = os.environ.get('DATABASE_URL')  # e.g. postgresql://postgres:pwd@db.ref.supabase.co:5432/postgres

if not DATABASE_URL:
        print('ERROR: Set DATABASE_URL environment variable (use service_role or postgres user)')
        sys.exit(2)

def run_sql_file(conn, path: Path):
        sql_text = path.read_text()
        # Run the SQL text as a single statement to preserve complex statements
        with conn.cursor() as cur:
                cur.execute(sql.SQL(sql_text))
        conn.commit()

def main():
        if not SCHEMA_FILE.exists():
                print(f'ERROR: schema file not found: {SCHEMA_FILE}')
                sys.exit(3)

        print('Connecting to database...')
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        try:
                print('Applying schema from', SCHEMA_FILE)
                run_sql_file(conn, SCHEMA_FILE)
                print('✅ Schema applied successfully')
        except Exception as exc:
                print('❌ Error applying schema:', exc)
                sys.exit(1)
        finally:
                conn.close()

if __name__ == '__main__':
        main()
```

3. Install the dependency and run locally:

```bash
pip install psycopg2-binary python-dotenv
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres \
    python scripts/apply_schema.py
```

Option B — Advanced: call a stored function via PostgREST RPC

1. One-time: create a secure stored function in Supabase (via SQL editor) that accepts SQL text and executes it. Example function — create this in the Supabase SQL editor once:

```sql
-- Run this once in Supabase SQL editor (be careful: SECURITY DEFINER grants powerful rights).
CREATE OR REPLACE FUNCTION public.run_sql(sql_text text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE sql_text;
    RETURN 'OK';
END;
$$;
```

Note: Because this function runs arbitrary SQL, keep it protected. Only call it with your `service_role` key from trusted environments.

2. Call the RPC endpoint from a local script using the PostgREST RPC path. Example Python script using `requests`:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ['SUPABASE_URL']  # https://<project-ref>.supabase.co
SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']

sql_text = open('scripts/schema.sql').read()

headers = {
        'apikey': SERVICE_KEY,
        'Authorization': f'Bearer {SERVICE_KEY}',
        'Content-Type': 'application/json'
}

resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/run_sql",
        json={'sql_text': sql_text},
        headers=headers
)

print(resp.status_code, resp.text)
```

3. Run locally (careful):

```bash
pip install requests python-dotenv
SUPABASE_URL=https://PROJECT_REF.supabase.co SUPABASE_SERVICE_KEY=your_service_role_key \
    python scripts/run_sql_rpc.py
```

Which option to choose?

- Use Option A if you want a straightforward, robust approach: connect with `psycopg2` and run SQL. It mirrors how typical migration tools operate and is easy to integrate into CI.
- Use Option B if you want to push SQL over HTTP and you already accept the one-time creation of a secure runner function. It's convenient for environments where direct DB connections are restricted.

Both approaches are run locally (or in CI) and do not use Vercel serverless functions — meeting your requirement to avoid serverless execution for schema changes.

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
- ✅ Check DATABASE_URL format: `postgresql://user:password@host:port/database`
- ✅ Verify Supabase project is running (not paused)
- ✅ Check firewall settings allow port 5432
- ✅ Ensure SSL mode is set to 'require'

#### 2. Cold Start Timeouts

**Problem**: Functions timeout on first request

**Solutions**:
- ✅ Add connection pooling configuration
- ✅ Use `pool_pre_ping=True` in SQLAlchemy settings
- ✅ Implement health check endpoint
- ✅ Consider upgrading Vercel plan for faster cold starts

#### 3. Static File Issues

**Problem**: CSS/JS files not loading

**Solutions**:
- ✅ Check static file paths in `api/index.py`
- ✅ Verify `static_folder` configuration
- ✅ Ensure files exist in `src/static/` directory
- ✅ Check CORS configuration

#### 4. Environment Variable Issues

**Problem**: Environment variables not accessible

**Solutions**:
- ✅ Verify variables are set in Vercel dashboard
- ✅ Check variable names match exactly (case-sensitive)
- ✅ Redeploy after adding new variables
- ✅ Use `os.environ.get()` with defaults

#### 5. SQLAlchemy Model Issues

**Problem**: Model fields not mapping correctly

**Solutions**:
- ✅ Check `__tablename__` matches Supabase table names
- ✅ Verify column types are PostgreSQL compatible
- ✅ Run schema sync script
- ✅ Check for naming conflicts (PostgreSQL is case-sensitive)

### Debugging Tips

1. **Enable Debug Logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Vercel Logs**:
   ```bash
   vercel logs --follow
   ```

3. **Test Database Connection**:
   ```python
   from sqlalchemy import create_engine
   engine = create_engine(DATABASE_URL)
   connection = engine.connect()
   result = connection.execute("SELECT version();")
   print(result.fetchone())
   ```

4. **Validate Environment Variables**:
   ```python
   import os
   print("DATABASE_URL:", os.environ.get('DATABASE_URL', 'NOT SET'))
   ```

## Best Practices

### 1. Security

- ✅ **Never commit secrets**: Use environment variables
- ✅ **Use strong passwords**: For database and secret keys
- ✅ **Enable SSL**: Always use `sslmode=require`
- ✅ **Limit API access**: Implement rate limiting if needed
- ✅ **Regular backups**: Supabase handles this automatically

### 2. Performance

- ✅ **Database indexing**: Add indexes for frequently queried columns
- ✅ **Connection pooling**: Configure SQLAlchemy pool settings
- ✅ **Query optimization**: Use efficient queries, avoid N+1 problems
- ✅ **Caching**: Consider implementing caching for static data
- ✅ **CDN usage**: Vercel automatically provides CDN for static assets

### 3. Monitoring

- ✅ **Health checks**: Implement `/health` endpoint
- ✅ **Error tracking**: Use services like Sentry for error monitoring
- ✅ **Performance monitoring**: Monitor response times and database performance
- ✅ **Logging**: Implement structured logging for better debugging

### 4. Development Workflow

- ✅ **Local development**: Use `.env` file for local testing
- ✅ **Staging environment**: Deploy to Vercel preview for testing
- ✅ **Version control**: Use Git branches for feature development
- ✅ **Database migrations**: Plan for schema changes
- ✅ **Testing**: Implement unit and integration tests

### 5. Scalability

- ✅ **Database optimization**: Monitor and optimize slow queries
- ✅ **Horizontal scaling**: Supabase and Vercel scale automatically
- ✅ **Caching strategies**: Implement Redis or similar for heavy workloads
- ✅ **API design**: Design stateless APIs for better scaling
- ✅ **Resource monitoring**: Watch database and function usage

## Conclusion

Congratulations! 🎉 You have successfully migrated your Flask NoteTaking application to a modern, cloud-based architecture using Vercel and Supabase. Your application now benefits from:

- **Global accessibility**: Available worldwide through Vercel's CDN
- **Automatic scaling**: Handles traffic spikes without configuration
- **Managed database**: PostgreSQL with automatic backups and scaling
- **Zero server maintenance**: Serverless architecture eliminates server management
- **Production-ready**: Built-in HTTPS, monitoring, and deployment workflows

### Next Steps

Consider these enhancements for your application:
1. **User Authentication**: Implement Supabase Auth for multi-user support
2. **Real-time Features**: Add live collaboration using Supabase real-time
3. **File Uploads**: Store attachments using Supabase Storage
4. **Advanced Search**: Implement full-text search using PostgreSQL features
5. **Mobile App**: Create React Native or Flutter app using Supabase APIs
6. **Analytics**: Add usage tracking and analytics
7. **API Rate Limiting**: Implement rate limiting for production use

Your application is now ready for production use and can scale to serve thousands of users! 🚀
