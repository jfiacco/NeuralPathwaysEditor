import sys

from NeuralPathways.app import PathwaysApp

if __name__ == '__main__':
    app = PathwaysApp(sys.argv)
    sys.exit(app.run())
