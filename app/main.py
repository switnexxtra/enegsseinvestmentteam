from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def index():
    return "running flask app"


if __name__ == '__main__':
    app.run()
