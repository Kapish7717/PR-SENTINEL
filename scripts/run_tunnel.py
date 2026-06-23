import os
import sys
import time
import logging

# Set up logging to stdout
logging.basicConfig(level=logging.DEBUG)

# Add parent directory to path to load .env
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env manually to fetch GITHUB_WEBHOOK_SECRET and potentially NGROK_AUTHTOKEN
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

try:
    import ngrok
    # Enable verbose ngrok client logging
    ngrok.log_level("debug")
except ImportError:
    print("Error: ngrok python package not installed. Run: pip install ngrok")
    sys.exit(1)

def main():
    authtoken = os.environ.get("NGROK_AUTHTOKEN")
    if authtoken:
        ngrok.set_auth_token(authtoken.strip())
        print("Configured Ngrok authtoken from .env.")
    else:
        print("No NGROK_AUTHTOKEN found in .env. Will attempt to use system-default configuration.")

    print("Establishing tunnel to http://localhost:8000...")

    try:
        listener = ngrok.forward(8000)
        public_url = listener.url()
        print("\n" + "=" * 60)
        print("🎉 NGROK TUNNEL ESTABLISHED SUCCESSFULLY!")
        print(f"Forwarding:  http://localhost:8000  -->  {public_url}")
        print(f"Webhook URL: {public_url}/webhook")
        print("=" * 60 + "\n")
        print("Press Ctrl+C to terminate the tunnel.")
        
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating tunnel...")
    except Exception as e:
        print(f"\nFailed to establish tunnel: {e}")
        print("\nTip: If you get an authtoken error, sign up for a free account at ngrok.com, ")
        print("copy your Authtoken, and add it to your .env file as:")
        print("NGROK_AUTHTOKEN=your_token_here")
        sys.exit(1)

if __name__ == "__main__":
    main()
