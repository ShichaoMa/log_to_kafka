from portalocker import lock, unlock, LOCK_EX, LOCK_NB, LockException

a = open("logs/test.lock", "w")
unlock(a)
unlock(a)
print 11111111
lock(a, LOCK_EX)
print 222222
unlock(a)