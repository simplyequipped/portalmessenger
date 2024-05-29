import os
import sys
import time
#import atexit
import argparse
import threading
import webbrowser

from http.server import BaseHTTPRequestHandler, HTTPServer

from . import create_app


#class RedirectHTTPRequestHandler(BaseHTTPRequestHandler):
#    def do_GET(self):
#        host_header = self.headers.get('Host')
#        
#        if host_header.endswith('.local'):
#            self.send_response(302)
#            self.send_header('Location', 'http://{}:{}{}'.format(host_header, redirect_port, self.path)
#            self.end_headers()


if __name__ == '__main__':
    program = 'python -m portalmessenger'
    epilog = 'Note: arguments specified when using --shortcut are included in the shortcut command'
    
    parser = argparse.ArgumentParser(prog=program, description='Messaging web app using pyjs8call', epilog=epilog)
    parser.add_argument('-a', '--host', help='Accept requests from this host address, defaults to 0.0.0.0 (all hosts)', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='Web server port, defaults to 5000', default=5000, type=int)
    parser.add_argument('-j', '--headless', help='Run JS8Call app headless (Linux only)', action='store_true')
    parser.add_argument('-s', '--settings', help='Path to pyjs8call settings file')
    parser.add_argument('-v', '--debug', help='Enable pyjs8call debug output', action='store_true')
    parser.add_argument('-b', '--browser', help='Open a browser window to 127.0.0.1 after starting server', action='store_true')
    parser.add_argument('-c', '--shortcut', help='Create a desktop shortcut to launch the application, then exit', action='store_true')
    parser.add_argument('-d', '--database', help='Path to portalmessenger database, defaults to ./.portal.sqlite')
    #parser.add_argument('-s', '--redirect', help='Redirect hostname.local requests from port 80 to the web server port', action='store_true')
    args = parser.parse_args()

    if args.shortcut:
        import pyshortcuts
        _os = pyshortcuts.uname # win, linux, or darwin

        #TODO create icon files, pyshortcuts falls back to python icon
        if _os in ['win', 'linux']:
            icon_file = '/static/icons/portalmessenger.ico'
        elif _os == 'darwin':
            icon_file = '/static/icons/portalmessenger.icns'
            
        icon_path = os.path.join( os.path.dirname( os.path.abspath(__file__) ), icon_file)
        
        # include specified args in pyshortcuts command, removing shortcut args
        sys_args = [arg for arg in sys.argv[1:] if arg.strip() not in ('--shortcut', '-c')]
        sys_args = ' '.join(sys_args)
        command = '{} -m portalmessenger ' + sys_args
        pyshortcuts.make_shortcut(command, name='Portal Messenger', icon=icon_path, terminal=True)

        print('\nDesktop shortcut created, exiting\n')
        exit()

#    if args.redirect:
#        httpd = HTTPServer(('', 80), RedirectHTTPRequestHandler)
#        atexit.register(httpd.shutdown)
#        print('Starting HTTP redirect server on port 80...')
#
#        thread = threading.Thread(target=httpd.serve_forever)
#        thread.daemon = True
#        thread.start()
    
    app, websockets = create_app(headless=args.headless, debugging=args.debug, pyjs8call_settings_path=args.settings, database_path=args.database)

    if args.browser:
        def delay_opening_browser():
            time.sleep(2)
            webbrowser.open('http://127.0.0.1:{}'.format(args.port))

        thread = threading.Thread(target=delay_opening_browser)
        thread.daemon = True
        thread.start()

    websockets.run(app, host=args.host, port=args.port, debug=False, allow_unsafe_werkzeug=True)
    
