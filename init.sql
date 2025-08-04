-- Database initialization script for Werewolf AI Game

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture TEXT,
    provider VARCHAR(50) NOT NULL DEFAULT 'google',
    free_games_remaining INTEGER NOT NULL DEFAULT 3,
    total_games_played INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create games table
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_config JSONB NOT NULL,
    game_state JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, completed, abandoned
    num_players INTEGER NOT NULL,
    current_phase VARCHAR(50),
    current_day INTEGER DEFAULT 1,
    winner VARCHAR(100),
    is_game_over BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create game_history table for detailed game events
CREATE TABLE IF NOT EXISTS game_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- game_start, player_action, phase_change, game_end
    event_data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    phase VARCHAR(50),
    day_count INTEGER
);

-- Create players table for game participants
CREATE TABLE IF NOT EXISTS players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_name VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    is_alive BOOLEAN DEFAULT TRUE,
    is_god BOOLEAN DEFAULT FALSE,
    ai_personality JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_games_user_id ON games(user_id);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_game_history_game_id ON game_history(game_id);
CREATE INDEX IF NOT EXISTS idx_game_history_timestamp ON game_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_players_game_id ON players(game_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a test user (optional, for development)
INSERT INTO users (email, name, provider, free_games_remaining) 
VALUES ('test@example.com', 'Test User', 'google', 3)
ON CONFLICT (email) DO NOTHING;

-- Create view for game statistics
CREATE OR REPLACE VIEW game_stats AS
SELECT 
    u.id as user_id,
    u.email,
    u.name,
    u.free_games_remaining,
    u.total_games_played,
    COUNT(g.id) as games_count,
    COUNT(CASE WHEN g.status = 'completed' THEN 1 END) as completed_games,
    COUNT(CASE WHEN g.status = 'active' THEN 1 END) as active_games,
    MAX(g.created_at) as last_game_date
FROM users u
LEFT JOIN games g ON u.id = g.user_id
GROUP BY u.id, u.email, u.name, u.free_games_remaining, u.total_games_played;
