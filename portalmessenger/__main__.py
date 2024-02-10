import os
import sys
import time
import argparse
import webbrowser

from . import create_app


if __name__ == '__main__':
    program = 'python -m portalmessenger'
    epilog = 'Note: other arguments specified when using --shortcut are included in the shortcut command'
    
    parser = argparse.ArgumentParser(prog=program, description='Messaging web app using pyjs8call', epilog=epilog)
    parser.add_argument('-a', '--host', help='Accept requests from this host address, defaults to 0.0.0.0 (all hosts)', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='Web server port, defaults to 5000', default=5000, type=int)
    parser.add_argument('-j', '--headless', help='Run JS8Call app headless (Linux only)', action='store_true')
    parser.add_argument('-c', '--config', help='Path to pyjs8call configuration file')
    parser.add_argument('-d', '--debug', help='Enable pyjs8call debug output', action='store_true')
    parser.add_argument('-b', '--browser', help='Open a browser window to 127.0.0.1 after starting server', action='store_true')
    parser.add_argument('-s', '--shortcut', help='Create a desktop shortcut to launch the application, then exit', action='store_true')
    args = parser.parse_args()
    sys_args = ' '.join(sys.argv[1:])

    if args.shortcut:
        import pyshortcuts
        _os = pyshortcuts.uname # win, linux, or darwin

        #TODO create icon files, pyshortcuts falls back to python icon
        if _os in ['win', 'linux']:
            icon_file = '/static/icons/portalmessenger.ico'
        elif _os == 'darwin':
            icon_file = '/static/icons/portalmessenger.icns'
            
        icon_path = os.path.join( os.path.dirname( os.path.abspath(__file__) ), icon_file)
        
        # include specified args in pyshortcuts command, removing --shortcut
        sys_args = sys_args.replace('--shortcut', '').replace('-s', '').replace('  ', ' ')
        command = '{} -m portalmessenger ' + sys_args
        pyshortcuts.make_shortcut(command, name='Portal Messenger', icon=icon_path, terminal=True)

        print('\nDesktop shortcut created, exiting\n')
        exit()
    
    app, websockets = create_app(headless=args.headless, debugging=args.debug, pyjs8call_config_path=args.config)

    if args.browser:
        webbrowser.open('http://127.0.0.1:{}'.format(args.port))

    websockets.run(app, host=args.host, port=args.port, debug=args.debug, allow_unsafe_werkzeug=True)
