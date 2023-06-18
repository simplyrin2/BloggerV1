from flask import Flask
import os

app=Flask(__name__)

if os.environ['ENV'] == 'development':
    app.config['ENV'] = 'development'
if os.environ['ENV'] == 'production':
    app.config['ENV'] = 'production'


if app.config['ENV'] == 'development':
    app.config.from_object('config.DevelopmentConfig')

elif app.config['ENV'] == 'production':
    app.config.from_object('config.ProductionConfig')

else:
    app.config.from_object('config.TestingConfig')
