import re

from flask import Flask, render_template, request, make_response

app = Flask(__name__)
application = app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/args')
def args():
    return render_template('args.html', request=request)


@app.route('/headers')
def headers():
    return render_template('headers.html', request=request)


@app.route('/cookies')
def cookies():
    resp = make_response(render_template('cookies.html', request=request))
    return resp


@app.route('/form', methods=['GET', 'POST'])
def form():
    return render_template('form.html', request=request)


def do_calc(operand1, operand2, action):
    if not operand1 or not operand2 or not action:
        return ''
    res = 0
    operand1 = int(operand1)
    operand2 = int(operand2)
    match action:
        case '+':
            res = operand1 + operand2
        case '-':
            res = operand1 - operand2
        case '*':
            res = operand1 * operand2
        case '/':
            res = operand1 / operand2
    return res


@app.route('/calc')
def calc():
    operand1 = request.args.get('operand1')
    operand2 = request.args.get('operand2')
    action = request.args.get('action')
    result = do_calc(operand1, operand2, action)
    return render_template('calc.html', result=result)


def validate_phone_number(phone):
    if not phone.startswith(('+7', '8')):
        return False, "Недопустимый ввод. Номер телефона должен начинаться с +7 или 8."
    clean = re.sub(pattern=r'[+\s().\-]', repl='', string=phone)
    if not clean.isdigit():
        return False, "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
    if (phone.startswith('+7') and len(clean) != 11) or (phone.startswith('8') and len(clean) != 10):
        return False, "Недопустимый ввод. Неверное количество цифр."

    return True, None


def format_phone(phone):
    clean = re.sub(pattern=r'[+\s().\-]', repl='', string=phone)[-10:]
    return f'8-{clean[:3]}-{clean[3:6]}-{clean[6:8]}-{clean[8:]}'


@app.route('/form_phone', methods=['GET', 'POST'])
def form_phone():
    if request.method == 'GET':
        return render_template('form_phone.html')

    phone_number = request.form['param1']
    is_valid, error_message = validate_phone_number(phone_number)
    if is_valid:
        formatted_phone = format_phone(phone_number)
        return render_template('form_phone.html', phone_number=phone_number, formatted_phone=formatted_phone)
    else:
        return render_template('form_phone.html', phone_number=phone_number, error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
