
import sys
if sys.version > '3':
    from gorgon import gorgon
else:
    import gorgon

if __name__ == '__main__':
    gorgon.run_cluster()
