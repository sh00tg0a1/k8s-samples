from flask import Flask
app = Flask(__name__)

N_OF_CALLS = 1


@app.route('/')
def hello():
    global N_OF_CALLS
    N_OF_CALLS += 1
    return "Hello World!, num_of_calls: {}".format(N_OF_CALLS)


@app.route('/<name>')
def hello_name(name):
    global N_OF_CALLS
    N_OF_CALLS += 1
    return "Hello {}!, num_of_calls: {}".format(name, N_OF_CALLS)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
