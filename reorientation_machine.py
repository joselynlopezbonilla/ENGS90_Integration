import threading
import HMI
import seek
import solenoid

if __name__ == '__main__':
    HMI = threading.Thread(name='hmi', target=HMI.main_HMI)
    seek = threading.Thread(name='pnp', target= seek.main_seek)

    HMI.start()
    seek.start()