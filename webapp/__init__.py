import waitress

def serve(**kwargs):
    waitress.serve(server.app,**kwargs)

def serve_local(port=5000, **kwargs):
    waitress.serve(server.app, host='localhost', port=port, **kwargs)

def serve_all(port=5000, **kwargs):
    waitress.serve(server.app, host='0.0.0.0', port=port, **kwargs)
