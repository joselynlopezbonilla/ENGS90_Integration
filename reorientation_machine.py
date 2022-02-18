import threading
import HMI
import seek

if __name__ == '__main__':
    #HMIThread = threading.Thread(name='hmi', target=HMI.main_HMI)
    seekThread = threading.Thread(name='pnp', target= seek.main_seek)

    print("after seek thread")

    # HMIThread.start()
    HMI.main_HMI()
    seekThread.start()
    # seek.start()