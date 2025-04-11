import os
import logging
from pygoop.proxy import create_app
from pygoop.utils import setup_logger

# Set up logger
logger = setup_logger("pygoop", logging.INFO)

# Create the app
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)