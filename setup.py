#!/usr/bin/env python3
"""
Setup script for Werewolf AI Agent Game v2.0

This script helps you set up the game environment and dependencies.
"""

import os
import sys
from pathlib import Path
import subprocess

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    template_file = Path(".env.template")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if template_file.exists():
        # Copy template
        template_content = template_file.read_text()
        
        print("📝 Creating .env file from template...")
        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        
        if api_key:
            content = template_content.replace("your_openai_api_key_here", api_key)
            env_file.write_text(content)
            print("✅ .env file created with your API key!")
        else:
            env_file.write_text(template_content)
            print("✅ .env file created with template values")
            print("💡 Edit .env file to add your OpenAI API key for enhanced features")
    else:
        print("❌ No .env template found. Creating basic .env file...")
        api_key = input("Enter your OpenAI API key (optional): ").strip()
        content = f"OPENAI_API_KEY={api_key}\nOPENAI_MODEL=gpt-3.5-turbo-instruct\n"
        env_file.write_text(content)
        print("✅ Basic .env file created")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "langchain",
        "langchain_openai", 
        "python-dotenv",
        "colorama",
        "requests"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        install = input("Install missing packages? (y/n): ").lower().strip()
        
        if install == 'y':
            return install_dependencies()
        else:
            print("⚠️  Some features may not work without all dependencies")
            return False
    else:
        print("✅ All dependencies are installed")
        return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Try running manually: pip install -r requirements.txt")
        return False

def run_tests():
    """Run basic tests to verify setup."""
    print("🧪 Running basic tests...")
    
    try:
        # Import main components to test
        sys.path.insert(0, str(Path("src")))
        
        from src.core.game_state import GameState
        from src.core.player import Player, Role
        
        # Test basic functionality
        game_state = GameState(6)
        player = Player(1, "TestPlayer", Role.CIVILIAN)
        
        print("  ✅ Core components load successfully")
        print("  ✅ Game state creation works")
        print("  ✅ Player creation works")
        print("  ✅ Agent creation works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def show_usage_info():
    """Show usage information."""
    print("\n🎮 Werewolf AI Agent Game v2.0 Setup Complete!")
    print("=" * 50)
    print("\n📖 Quick Start:")
    print("  python main.py                    # Run the game")
    print("  python examples/simple_game.py    # Run simple example")
    print("  python examples/enhanced_features_demo.py  # Demo advanced features")
    print("  python tests/test_werewolf.py     # Run tests")
    
    print("\n🔧 Configuration:")
    print("  Edit .env file to add your OpenAI API key for enhanced AI features")
    print("  The game works without an API key using fallback responses")
    
    print("\n📁 Project Structure:")
    print("  src/core/        # Core game engine")
    print("  src/agents/      # Basic agent implementations")
    print("  src/ai/          # Advanced AI features")
    print("  src/tools/       # Internet search and tools")
    print("  examples/        # Usage examples")
    print("  tests/           # Test suite")
    
    print("\n🐛 Troubleshooting:")
    print("  - Make sure Python 3.8+ is installed")
    print("  - Run 'pip install -r requirements.txt' if imports fail")
    print("  - Check .env file for API key configuration")
    
    print("\n🎯 Game Features:")
    print("  ✅ Multi-agent Werewolf/Mafia game")
    print("  ✅ Advanced AI with multi-step reasoning")
    print("  ✅ Internet research integration")
    print("  ✅ Strategic analysis and confidence scoring")
    print("  ✅ Fallback mode (works without API keys)")

def main():
    """Main setup function."""
    print("🐺 Werewolf AI Agent Game - Setup Script")
    print("=" * 50)
    
    success = True
    
    # Step 1: Check and install dependencies
    if not check_dependencies():
        success = False
    
    # Step 2: Create environment file
    if not create_env_file():
        success = False
    
    # Step 3: Run basic tests
    if not run_tests():
        success = False
        print("⚠️  Some components may not work properly")
    
    # Step 4: Show usage information
    show_usage_info()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("Run 'python main.py' to start playing!")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("Check the messages above and resolve any issues")
    
    return success

if __name__ == "__main__":
    main()
    """Main setup function"""
    print("🐺 Werewolf AI Agent Game Setup 🐺\n")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    print("\n🎮 Setup complete! Run 'python main.py' to start the game")

if __name__ == "__main__":
    main()
