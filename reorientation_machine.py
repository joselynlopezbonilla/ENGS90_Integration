import threading
import HMI
import seek

if __name__ == '__main__':
    #HMI = threading.Thread(name='hmi', target=HMI.main_HMI)
    seek = threading.Thread(name='pnp', target= seek.main_seek)

    #HMI.start()
    HMI.main_HMI()
    seek.start()