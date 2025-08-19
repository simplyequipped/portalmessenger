import os
import sys
import time
import argparse
import threading
import webbrowser
from .server import run_server
from .database import get_database, close_database


def main():
    parser = argparse.ArgumentParser(
        prog='portalmessenger', 
        description='HF radio messaging web app using pyjs8call', 
        epilog='Note: arguments specified when using --shortcut are included in the shortcut command'
    )
    
    parser.add_argument('-a', '--host', help='Accept requests from this host address, defaults to 0.0.0.0 (all hosts)', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='Web server port, defaults to 5000', default=5000, type=int)
    parser.add_argument('-b', '--browser', help='Open a browser window to localhost after starting server', action='store_true')
    parser.add_argument('-c', '--shortcut', help='Create a desktop shortcut to launch the application, then exit', action='store_true')
    parser.add_argument('-d', '--database', help='Path to portalmessenger database, defaults to ./portalmessenger.json', default='portalmessenger.json')
    parser.add_argument('--debug', help='Enable debug logging for server and networking', action='store_true')
    args = parser.parse_args()

    if args.shortcut:
        create_desktop_shortcut(args)
        return

    try:
        db = get_database(args.database)
    except Exception as e:
        print(f'Error initializing database: {e}')
        sys.exit(1)

    if args.browser:
        def delay_opening_browser():
            time.sleep(2)
            webbrowser.open(f'http://localhost:{args.port}')

        thread = threading.Thread(target=delay_opening_browser)
        thread.daemon = True
        thread.start()

    print(f'Starting Portal Messenger on {args.host}:{args.port}')
    
    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print('\nShutting down...')
    finally:
        close_database()


def create_desktop_shortcut(args):
    '''Create a desktop shortcut for the application'''
    try:
        import pyshortcuts
        _os = pyshortcuts.uname  # win, linux, or darwin

        if _os == 'win':
            icon_file = 'static\\icons\\portalmessenger.ico'
        elif _os == 'linux':
            icon_file = 'static/icons/portalmessenger.png'
        elif _os == 'darwin':
            icon_file = 'static/icons/portalmessenger.icns'
        else:
            icon_file = 'static/icons/portalmessenger.png'

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_file)

        # nclude specified args in pyshortcuts command, removing shortcut args
        sys_args = [arg for arg in sys.argv[1:] if arg.strip() not in ('--shortcut', '-c')]
        sys_args = ' '.join(sys_args)
        command = f'{sys.executable} -m portalmessenger {sys_args}'
        
        pyshortcuts.make_shortcut(
            command, 
            name='Portal Messenger', 
            icon=icon_path, 
            terminal=True
        )

        print('\nDesktop shortcut created, exiting\n')
    
    except ImportError:
        print('Error: pyshortcuts not installed. Cannot create desktop shortcut.')
        sys.exit(1)
    except Exception as e:
        print(f'Error creating desktop shortcut: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
