# Werewolf AI Game - Authentication Setup Guide

## Overview
This guide will help you set up Google OAuth and other authentication methods for your Werewolf AI Game.

## Prerequisites
- Google Cloud Console account
- Node.js and npm installed
- Python 3.8+ installed

## 🔧 Backend Setup

### 1. Install Dependencies
```bash
cd /path/to/werewolf
pip install authlib python-jose[cryptography] passlib[bcrypt]
```

### 2. Create Environment File
```bash
cp .env.example .env
```

### 3. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized origins:
   - `http://localhost:3000` (for development)
   - Your production domain
7. Add authorized redirect URIs:
   - `http://localhost:3000` (for development)
   - Your production domain
8. Copy the Client ID and Client Secret

### 4. Update .env File
```bash
SECRET_KEY="your-very-long-secret-key-here-make-it-secure"
GOOGLE_CLIENT_ID="your-google-client-id-here"
GOOGLE_CLIENT_SECRET="your-google-client-secret-here"
```

## 🎨 Frontend Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Create Frontend Environment File
```bash
cp .env.example .env
```

### 3. Update Frontend .env File
```bash
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id-here
```

## 🚀 Running the Application

### 1. Start Backend Server
```bash
# From the root directory
python app.py
```

### 2. Start Frontend Development Server
```bash
# From the frontend directory
cd frontend
npm start
```
