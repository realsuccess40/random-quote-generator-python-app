from flask import Flask, render_template
import random

app = Flask(__name__)

quotes = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Success is the sum of small efforts, repeated day in and day out. - Robert Collier",
    "It always seems impossible until it's done. - Nelson Mandela",
    "In the middle of every difficulty lies opportunity. - Albert Einstein",
    "You do not find the happy life. You make it. - Camilla Kimball",
    "Dream big and dare to fail. - Norman Vaughan",
    "Your limitation—it is only your imagination. - Anonymous",
    "Push yourself, because no one else is going to do it for you. - Unknown"
]

@app.route('/')
def home():
    random_quote = random.choice(quotes)
    return render_template('index.html', quote=random_quote)

if __name__ == '__main__':
    app.run(debug=True)
