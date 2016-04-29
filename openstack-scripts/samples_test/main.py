from multiprocessing import *
import multiprocessing

def myfunction(a,b,q):

    c = a * b
    q.put(c)

def main():
    jobs=[]
    q = Queue()
    for i in range(2):
        p = Process(target=myfunction,args = (2,3,q))
        jobs.append(p)
        p.start()
        print q.get()


if __name__ == '__main__':
    main()