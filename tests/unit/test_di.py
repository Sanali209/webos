import abc
import pytest
import threading
from src.core.di import DIContainer, Lifetime, CircularDependencyError, ServiceNotFoundError

class IService(abc.ABC):
    @abc.abstractmethod
    def foo(self):
        pass

class ServiceA(IService):
    def foo(self):
        return "bar"

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

class ServiceC:
    def __init__(self, b: ServiceB):
        self.b = b

class CircularA:
    def __init__(self, b: 'CircularB'):
        self.b = b

class CircularB:
    def __init__(self, a: CircularA):
        self.a = a

def test_singleton_lifetime():
    container = DIContainer()
    container.register(ServiceA, lifetime=Lifetime.SINGLETON)
    
    instance1 = container.resolve(ServiceA)
    instance2 = container.resolve(ServiceA)
    
    assert instance1 is instance2
    assert isinstance(instance1, ServiceA)

def test_transient_lifetime():
    container = DIContainer()
    container.register(ServiceA, lifetime=Lifetime.TRANSIENT)
    
    instance1 = container.resolve(ServiceA)
    instance2 = container.resolve(ServiceA)
    
    assert instance1 is not instance2
    assert isinstance(instance1, ServiceA)

def test_constructor_injection():
    container = DIContainer()
    container.register(ServiceA)
    container.register(ServiceB)
    
    instance_b = container.resolve(ServiceB)
    assert isinstance(instance_b, ServiceB)
    assert isinstance(instance_b.a, ServiceA)

def test_deep_injection():
    container = DIContainer()
    container.register(ServiceA)
    container.register(ServiceB)
    container.register(ServiceC)
    
    instance_c = container.resolve(ServiceC)
    assert isinstance(instance_c, ServiceC)
    assert isinstance(instance_c.b, ServiceB)
    assert isinstance(instance_c.b.a, ServiceA)

def test_circular_dependency():
    container = DIContainer()
    container.register(CircularA)
    container.register(CircularB)
    
    with pytest.raises(CircularDependencyError):
        container.resolve(CircularA)

def test_service_not_found():
    container = DIContainer()
    with pytest.raises(ServiceNotFoundError):
        container.resolve(IService)

def test_auto_registration():
    container = DIContainer()
    instance = container.resolve(ServiceA)
    assert isinstance(instance, ServiceA)

def test_scoped_lifetime():
    container = DIContainer()
    container.register(ServiceA, lifetime=Lifetime.SCOPED)
    
    instance1 = None
    instance2 = None
    
    def thread1():
        nonlocal instance1
        instance1 = container.resolve(ServiceA)
        assert container.resolve(ServiceA) is instance1
        
    def thread2():
        nonlocal instance2
        instance2 = container.resolve(ServiceA)
        assert container.resolve(ServiceA) is instance2

    t1 = threading.Thread(target=thread1)
    t2 = threading.Thread(target=thread2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    assert instance1 is not instance2

def test_inject_decorator():
    container = DIContainer()
    container.register(ServiceA)
    
    @container.inject
    def my_func(a: ServiceA, other: str = "default"):
        return a, other
    
    a_inst, val = my_func()
    assert isinstance(a_inst, ServiceA)
    assert val == "default"
    
    manual_a = ServiceA()
    a_inst2, val2 = my_func(a=manual_a, other="manual")
    assert a_inst2 is manual_a
    assert val2 == "manual"
