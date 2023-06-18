source .venv/bin/activate
export ENV=development
export DATABASE_URI=sqlite:///database.sqlite3
export SECRET_KEY=iamasecretkey1234!@#$
export UPLOADS=/home/inpat/BloggerApp/static/images/uploads
export JWT_SECRET_KEY=thisisasecretkey

# python api.py
python main.py