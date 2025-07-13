from invoice_scanner_api import app
import os

# This is the Flask app that will be used by gunicorn
# The app is imported from invoice_scanner_api.py

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False) 