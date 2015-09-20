
## setup
```bash
# Install virtualenv (https://virtualenv.pypa.io/en/latest/installation.html)
pip install virtualenv
virtualenv --no-site-packages -p /usr/bin/python3 env
# If you're on a mac, try just: virtualenv --no-site-packages env
source env/bin/activate
pip install -r requirements.txt
# to set up database:
python setup.py
```

## start server
```bash
python reviews.py
# or
gunicorn reviews:app
```
