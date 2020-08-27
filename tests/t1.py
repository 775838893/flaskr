

def wrap1(func):
    print('in wrap1')
    def inner1(*args,**kwargs):
        print('inner1')
        ret1 =  func(*args,**kwargs)
        print('end inner1',ret1)
        return ret1
    print('1',inner1)
    return inner1

def wrap2(func):
    print('in wrap2')
    def inner2(*args,**kwargs):
        print('inner2')
        ret2 =  func(*args,**kwargs)
        print('end inner2',ret2)
        return ret2
    return inner2

@wrap1
@wrap2
def f(x):
    print('in f')
    return x+1

f(1)