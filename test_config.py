#!/usr/bin/env python3
"""
Test script to validate VintedScanner configuration
"""
import sys
import os

def test_config():
    """Test configuration file"""
    try:
        import Config
        print("✅ Config.py loaded successfully")
        
        # Test Telegram configuration
        if hasattr(Config, 'telegram_bot_token') and Config.telegram_bot_token:
            print("✅ Telegram bot token configured")
        else:
            print("❌ Telegram bot token missing")
            
        if hasattr(Config, 'telegram_chat_id') and Config.telegram_chat_id:
            print("✅ Telegram chat ID configured")
        else:
            print("❌ Telegram chat ID missing")
            
        # Test topics configuration
        if hasattr(Config, 'topics') and Config.topics:
            print(f"✅ Found {len(Config.topics)} configured topics")
            for topic_name, topic_data in Config.topics.items():
                if 'thread_id' in topic_data and 'query' in topic_data:
                    print(f"  ✅ {topic_name}: valid configuration")
                else:
                    print(f"  ❌ {topic_name}: invalid configuration")
        else:
            print("❌ No topics configured")
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Config.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    dependencies = ['requests', 'telegram']
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} module available")
        except ImportError:
            print(f"❌ {dep} module missing")
            return False
    
    return True

def main():
    print("🔧 VintedScanner Configuration Test")
    print("=" * 40)
    
    config_ok = test_config()
    print()
    deps_ok = test_dependencies()
    
    print("\n" + "=" * 40)
    if config_ok and deps_ok:
        print("✅ All tests passed! VintedScanner is ready to run.")
    else:
        print("❌ Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
