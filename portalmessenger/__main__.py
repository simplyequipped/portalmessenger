from . import create_app

if __name__ == '__main__':
    app, websockets = create_app()
    websockets.run(app, host='0.0.0.0')
