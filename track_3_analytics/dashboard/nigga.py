# Source - https://stackoverflow.com/a
# Posted by Zorayr, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-13, License - CC BY-SA 4.0

from multiprocessing import Process

server = Process(target=app.run)
server.start()
# ...
server.terminate()
server.join()

