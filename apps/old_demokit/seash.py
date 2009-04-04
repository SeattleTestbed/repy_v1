""" 
Author: Justin Cappos

Module: A shell for Seattle called seash (pronounced see-SHH).   It's not meant
        to be the perfect shell, but it should be good enough for v0.1

Start date: September 18th, 2008

This is an example experiment manager for Seattle.   It allows a user to 
locate vessels they control and manage those vessels.

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

Note: I've written this assuming that repy <-> python integration is perfect
and transparent (minus the bit of mess that fixes this).   As a result this
code may change significantly in the future.

This module is a mess.   The big problem is that we have ~ 30 lines of input
parsing for everything the user does followed by ~ 5 lines of code.   I'm not
sure how to fix this or structure this module to make it cleaner...
"""

# simple client.   A better test client (but nothing like what a real client
# would be)

### Integration fix here...
from repyportability import *


#begin include nmclient.repy
""" 
Author: Justin Cappos

Module: Routines that interact with a node manager to perform actions on
        nodes.   A simple front end can be added to make this a functional
        experiment manager.

Start date: September 7th 2008

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

"""

# for signing the data we send to the node manager
#begin include signeddata.repy
""" Justin Cappos -- routines that create and verify signatures and prevent
replay / freeze / out of sequence / misdelivery attacks

Replay attack:   When someone provides information you signed before to try
to get you to perform an old action again.   For example, A sends messages to
the node manager to provide a vessel to B (B intercepts this traffic).   Later 
A acquires the vessel again.   B should not be able to replay the messages A 
sent to the node manager to have the vessel transferred to B again.

Freeze attack:   When an attacker can act as a man-in-the-middle and provide
stale information to an attacker.   For example, B can intercept all traffic
between the node manager and A.   If C makes a change on the node manager, then
B should not be able to prevent A from seeing the change (at least within 
some time bound).

Out of sequence attack:   When someone can skip sending some messages but
deliver others.   For example, A wants to stop the current program, upload
a new copy of the program, and start the program again.   It should be possible
for A to specify that these actions must be performed in order and without 
skipping any of the prior actions (regardless of failures, etc.).

Misdelivery attack:   Messages should only be acted upon by the nodes that 
the user intended.   A malicious party should not be able to "misdeliver" a
message and have a different node perform the action.



I have support for "sequence numbers" which will require that intermediate 
events are not skipped.    The sequence numbers are a tuple: (tag, version)

"""


#begin include sha.repy
#!/usr/bin/env python
# -*- coding: iso-8859-1

"""A sample implementation of SHA-1 in pure Python.

   Adapted by Justin Cappos from the version at: http://codespeak.net/pypy/dist/pypy/lib/sha.py

   Framework adapted from Dinu Gherman's MD5 implementation by
   J. Hall`en and L. Creighton. SHA-1 implementation based directly on
   the text of the NIST standard FIPS PUB 180-1.

date    = '2004-11-17'
version = 0.91 # Modernised by J. Hall`en and L. Creighton for Pypy
"""



# ======================================================================
# Bit-Manipulation helpers
#
#   _long2bytes() was contributed by Barry Warsaw
#   and is reused here with tiny modifications.
# ======================================================================

def _sha_long2bytesBigEndian(n, thisblocksize=0):
    """Convert a long integer to a byte string.

    If optional blocksize is given and greater than zero, pad the front
    of the byte string with binary zeros so that the length is a multiple
    of blocksize.
    """

    # Justin: I changed this to avoid using pack. I didn't test performance, etc
    s = ''
    while n > 0:
        #original: 
        # s = struct.pack('>I', n & 0xffffffffL) + s
        # n = n >> 32
        s = chr(n & 0xff) + s
        n = n >> 8

    # Strip off leading zeros.
    for i in range(len(s)):
        if s[i] <> '\000':
            break
    else:
        # Only happens when n == 0.
        s = '\000'
        i = 0

    s = s[i:]

    # Add back some pad bytes. This could be done more efficiently
    # w.r.t. the de-padding being done above, but sigh...
    if thisblocksize > 0 and len(s) % thisblocksize:
        s = (thisblocksize - len(s) % thisblocksize) * '\000' + s

    return s


def _sha_bytelist2longBigEndian(list):
    "Transform a list of characters into a list of longs."

    imax = len(list)/4
    hl = [0L] * imax

    j = 0
    i = 0
    while i < imax:
        b0 = long(ord(list[j])) << 24
        b1 = long(ord(list[j+1])) << 16
        b2 = long(ord(list[j+2])) << 8
        b3 = long(ord(list[j+3]))
        hl[i] = b0 | b1 | b2 | b3
        i = i+1
        j = j+4

    return hl


def _sha_rotateLeft(x, n):
    "Rotate x (32 bit) left n bits circularly."

    return (x << n) | (x >> (32-n))


# ======================================================================
# The SHA transformation functions
#
# ======================================================================

# Constants to be used
sha_K = [
    0x5A827999L, # ( 0 <= t <= 19)
    0x6ED9EBA1L, # (20 <= t <= 39)
    0x8F1BBCDCL, # (40 <= t <= 59)
    0xCA62C1D6L  # (60 <= t <= 79)
    ]

class sha:
    "An implementation of the MD5 hash function in pure Python."

    def __init__(self):
        "Initialisation."
        
        # Initial message length in bits(!).
        self.length = 0L
        self.count = [0, 0]

        # Initial empty message as a sequence of bytes (8 bit characters).
        self.inputdata = []

        # Call a separate init function, that can be used repeatedly
        # to start from scratch on the same object.
        self.init()


    def init(self):
        "Initialize the message-digest and set all fields to zero."

        self.length = 0L
        self.inputdata = []

        # Initial 160 bit message digest (5 times 32 bit).
        self.H0 = 0x67452301L
        self.H1 = 0xEFCDAB89L
        self.H2 = 0x98BADCFEL
        self.H3 = 0x10325476L
        self.H4 = 0xC3D2E1F0L

    def _transform(self, W):

        for t in range(16, 80):
            W.append(_sha_rotateLeft(
                W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16], 1) & 0xffffffffL)

        A = self.H0
        B = self.H1
        C = self.H2
        D = self.H3
        E = self.H4

        """
        This loop was unrolled to gain about 10% in speed
        for t in range(0, 80):
            TEMP = _sha_rotateLeft(A, 5) + sha_f[t/20] + E + W[t] + sha_K[t/20]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL
        """

        for t in range(0, 20):
            TEMP = _sha_rotateLeft(A, 5) + ((B & C) | ((~ B) & D)) + E + W[t] + sha_K[0]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL

        for t in range(20, 40):
            TEMP = _sha_rotateLeft(A, 5) + (B ^ C ^ D) + E + W[t] + sha_K[1]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL

        for t in range(40, 60):
            TEMP = _sha_rotateLeft(A, 5) + ((B & C) | (B & D) | (C & D)) + E + W[t] + sha_K[2]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL

        for t in range(60, 80):
            TEMP = _sha_rotateLeft(A, 5) + (B ^ C ^ D)  + E + W[t] + sha_K[3]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL


        self.H0 = (self.H0 + A) & 0xffffffffL
        self.H1 = (self.H1 + B) & 0xffffffffL
        self.H2 = (self.H2 + C) & 0xffffffffL
        self.H3 = (self.H3 + D) & 0xffffffffL
        self.H4 = (self.H4 + E) & 0xffffffffL
    

    # Down from here all methods follow the Python Standard Library
    # API of the sha module.

    def update(self, inBuf):
        """Add to the current message.

        Update the md5 object with the string arg. Repeated calls
        are equivalent to a single call with the concatenation of all
        the arguments, i.e. m.update(a); m.update(b) is equivalent
        to m.update(a+b).

        The hash is immediately calculated for all full blocks. The final
        calculation is made in digest(). It will calculate 1-2 blocks,
        depending on how much padding we have to add. This allows us to
        keep an intermediate value for the hash, so that we only need to
        make minimal recalculation if we call update() to add more data
        to the hashed string.
        """

        leninBuf = long(len(inBuf))

        # Compute number of bytes mod 64.
        index = (self.count[1] >> 3) & 0x3FL

        # Update number of bits.
        self.count[1] = self.count[1] + (leninBuf << 3)
        if self.count[1] < (leninBuf << 3):
            self.count[0] = self.count[0] + 1
        self.count[0] = self.count[0] + (leninBuf >> 29)

        partLen = 64 - index

        if leninBuf >= partLen:
            self.inputdata[index:] = list(inBuf[:partLen])
            self._transform(_sha_bytelist2longBigEndian(self.inputdata))
            i = partLen
            while i + 63 < leninBuf:
                self._transform(_sha_bytelist2longBigEndian(list(inBuf[i:i+64])))
                i = i + 64
            else:
                self.inputdata = list(inBuf[i:leninBuf])
        else:
            i = 0
            self.inputdata = self.inputdata + list(inBuf)


    def digest(self):
        """Terminate the message-digest computation and return digest.

        Return the digest of the strings passed to the update()
        method so far. This is a 16-byte string which may contain
        non-ASCII characters, including null bytes.
        """

        H0 = self.H0
        H1 = self.H1
        H2 = self.H2
        H3 = self.H3
        H4 = self.H4
        inputdata = [] + self.inputdata
        count = [] + self.count

        index = (self.count[1] >> 3) & 0x3fL

        if index < 56:
            padLen = 56 - index
        else:
            padLen = 120 - index

        padding = ['\200'] + ['\000'] * 63
        self.update(padding[:padLen])

        # Append length (before padding).
        bits = _sha_bytelist2longBigEndian(self.inputdata[:56]) + count

        self._transform(bits)

        # Store state in digest.
        digest = _sha_long2bytesBigEndian(self.H0, 4) + \
                 _sha_long2bytesBigEndian(self.H1, 4) + \
                 _sha_long2bytesBigEndian(self.H2, 4) + \
                 _sha_long2bytesBigEndian(self.H3, 4) + \
                 _sha_long2bytesBigEndian(self.H4, 4)

        self.H0 = H0 
        self.H1 = H1 
        self.H2 = H2
        self.H3 = H3
        self.H4 = H4
        self.inputdata = inputdata 
        self.count = count 

        return digest


    def hexdigest(self):
        """Terminate and return digest in HEX form.

        Like digest() except the digest is returned as a string of
        length 32, containing only hexadecimal digits. This may be
        used to exchange the value safely in email or other non-
        binary environments.
        """
        return ''.join(['%02x' % ord(c) for c in self.digest()])

    def copy(self):
        """Return a clone object. (not implemented)

        Return a copy ('clone') of the md5 object. This can be used
        to efficiently compute the digests of strings that share
        a common initial substring.
        """
        raise Exception, "not implemented"


# ======================================================================
# Mimic Python top-level functions from standard library API
# for consistency with the md5 module of the standard library.
# ======================================================================

# These are mandatory variables in the module. They have constant values
# in the SHA standard.

sha_digest_size = sha_digestsize = 20
sha_blocksize = 1

def sha_new(arg=None):
    """Return a new sha crypto object.

    If arg is present, the method call update(arg) is made.
    """

    crypto = sha()
    if arg:
        crypto.update(arg)

    return crypto


# gives the hash of a string
def sha_hash(string):
    crypto = sha()
    crypto.update(string)
    return crypto.digest()


# gives the hash of a string
def sha_hexhash(string):
    crypto = sha()
    crypto.update(string)
    return crypto.hexdigest()
#end include sha.repy
#begin include rsa.repy
"""RSA module

Adapted by Justin Cappos from the version by:
author = "Sybren Stuvel, Marloes de Boer and Ivo Tamboer"
date = "2008-04-23"


All of the base64 encoding, pickling, and zlib encoding has been removed
"""


# NOTE: Python's modulo can return negative numbers. We compensate for
# this behaviour using the abs() function

#begin include random.repy
""" Random routines (similar to random in Python)
Author: Justin Cappos


"""

def random_randint(minvalue, maxvalue):

  if minvalue > maxvalue:
    # mimic random's failure behaviour
    raise ValueError, "empty range for randrange()"

  if maxvalue == minvalue:
    return maxvalue

  randomrange = maxvalue - minvalue

  # get a small random number
  randomnumber = int(randomfloat() * 2**32)

  # We're going to generate the number 32 bits at a time...
  while randomrange > 2**32:
    # add random bits to the bottom...
    randomnumber = (randomnumber << 32) + int(randomfloat() * 2**32)
    # shift the range
    randomrange = randomrange >> 32

  # BUG: doing mod here isn't perfect.   If there are 32 bits to make random,
  # and the range isn't a power of 2, some numbers will be slightly more likely
  # than others...   I could detect and retry I guess...
  retvalue = minvalue + (randomnumber % (maxvalue - minvalue + 1))
  assert(minvalue<=retvalue<=maxvalue)
  return retvalue


def random_sample(population, k):
  newpopulation = population[:]
  if len(population) < k:
    raise ValueError, "sample larger than population"

  retlist = []
  populationsize = len(population)-1

  for num in range(k):
    pos = random_randint(0,populationsize-num)
    retlist.append(newpopulation[pos])
    del newpopulation[pos]

  return retlist
#end include random.repy

#begin include math.repy
""" Justin Cappos -- substitute for a few python math routines"""

def math_ceil(x):
  xint = int(x)
  
  # if x is positive and not equal to itself truncated then we should add 1
  if x > 0 and x != xint:
    xint = xint + 1

  # I return a float because math.ceil does
  return float(xint)



def math_floor(x):
  xint = int(x)
  
  # if x is negative and not equal to itself truncated then we should subtract 1
  if x < 0 and x != xint:
    xint = xint - 1

  # I return a float because math.ceil does
  return float(xint)



math_e = 2.7182818284590451
math_pi = 3.1415926535897931

# stolen from a link off of wikipedia (http://en.literateprograms.org/Logarithm_Function_(Python)#chunk use:logN.py)
# MIT license
#
# hmm, math_log(4.5,4)      == 1.0849625007211561
# Python's math.log(4.5,4)  == 1.0849625007211563
# I'll assume this is okay.
def math_log(X, base=math_e, epsilon=1e-16):
  # log is logarithm function with the default base of e
  integer = 0
  if X < 1 and base < 1:
    # BUG: the cmath implementation can handle smaller numbers...
    raise ValueError, "math domain error"
  while X < 1:
    integer -= 1
    X *= base
  while X >= base:
    integer += 1
    X /= base
  partial = 0.5               # partial = 1/2 
  X *= X                      # We perform a squaring
  decimal = 0.0
  while partial > epsilon:
    if X >= base:             # If X >= base then a_k is 1 
      decimal += partial      # Insert partial to the front of the list
      X = X / base            # Since a_k is 1, we divide the number by the base
    partial *= 0.5            # partial = partial / 2
    X *= X                    # We perform the squaring again
  return (integer + decimal)

#end include math.repy



def rsa_gcd(p, q):
    """Returns the greatest common divisor of p and q


    >>> gcd(42, 6)
    6
    """
    if p<q: return rsa_gcd(q, p)
    if q == 0: return p
    return rsa_gcd(q, abs(p%q))

def rsa_bytes2int(bytes):
    """Converts a list of bytes or a string to an integer

    >>> (128*256 + 64)*256 + + 15
    8405007
    >>> l = [128, 64, 15]
    >>> bytes2int(l)
    8405007
    """

    if not (type(bytes) is list or type(bytes) is str):
        raise TypeError("You must pass a string or a list")

    # there is a bug here that strings with leading \000 have the leading char
    # stripped away.   I need to fix that.  To fix it, I prepend \001 to 
    # everything I process.   I also have to ensure I'm passed a small enough
    # chunk that it all still fits (fix for that where I'm called).
    bytes = '\001' + bytes

    # Convert byte stream to integer
    integer = 0
    for byte in bytes:
        integer *= 256
        # this used to be StringType which includes unicode, however, this
        # loop doesn't correctly handle unicode data, so the change should also
        # be a bug fix
        if type(byte) is str: byte = ord(byte)
        integer += byte

    return integer

def rsa_int2bytes(number):
    """Converts a number to a string of bytes
    
    >>> bytes2int(int2bytes(123456789))
    123456789
    """

    if not (type(number) is long or type(number) is int):
        raise TypeError("You must pass a long or an int")

    string = ""

    while number > 0:
        string = "%s%s" % (chr(number & 0xFF), string)
        number /= 256
    
    if string[0] != '\001':
        raise TypeError("Invalid RSA data")
 
    return string[1:]

def rsa_fast_exponentiation(a, p, n):
    """Calculates r = a^p mod n
    """
    result = a % n
    remainders = []
    while p != 1:
        remainders.append(p & 1)
        p = p >> 1
    while remainders:
        rem = remainders.pop()
        result = ((a ** rem) * result ** 2) % n
    return result

def rsa_fermat_little_theorem(p):
    """Returns 1 if p may be prime, and something else if p definitely
    is not prime"""

    a = random_randint(1, p-1)
    return rsa_fast_exponentiation(a, p-1, p)

def rsa_jacobi(a, b):
    """Calculates the value of the Jacobi symbol (a/b)
    """

    if a % b == 0:
        return 0
    result = 1
    while a > 1:
        if a & 1:
            if ((a-1)*(b-1) >> 2) & 1:
                result = -result
            b, a = a, b % a
        else:
            if ((b ** 2 - 1) >> 3) & 1:
                result = -result
            a = a >> 1
    return result

def rsa_jacobi_witness(x, n):
    """Returns False if n is an Euler pseudo-prime with base x, and
    True otherwise.
    """

    j = rsa_jacobi(x, n) % n
    f = rsa_fast_exponentiation(x, (n-1)/2, n)

    if j == f: return False
    return True

def rsa_randomized_primality_testing(n, k):
    """Calculates whether n is composite (which is always correct) or
    prime (which is incorrect with error probability 2**-k)

    Returns False if the number if composite, and True if it's
    probably prime.
    """

    q = 0.5     # Property of the jacobi_witness function

    t = int(math_ceil(k / math_log(1/q, 2)))
    for junk in range(t+1):
        # JAC: Sometimes we get a ValueError here because the range is empty 
        # (i.e. we are doing randint(1,1) or randint (1,0), etc.).   I'll check
        # and return False in this case and declare 1 and 2 composite (since 
        # they make horrible p or q in RSA).
        if n-1 < 2:
          return False
        x = random_randint(1, n-1)
        if rsa_jacobi_witness(x, n): return False
    
    return True

def rsa_is_prime(number):
    """Returns True if the number is prime, and False otherwise.

    >>> rsa_is_prime(42)
    0
    >>> rsa_is_prime(41)
    1
    """

    """
    if not fermat_little_theorem(number) == 1:
        # Not prime, according to Fermat's little theorem
        return False
    """

    if rsa_randomized_primality_testing(number, 5):
        # Prime, according to Jacobi
        return True
    
    # Not prime
    return False

    
def rsa_getprime(nbits):
    """Returns a prime number of max. 'math_ceil(nbits/8)*8' bits. In
    other words: nbits is rounded up to whole bytes.

    >>> p = getprime(8)
    >>> rsa_is_prime(p-1)
    0
    >>> rsa_is_prime(p)
    1
    >>> rsa_is_prime(p+1)
    0
    """

    while True:
#        integer = read_random_int(nbits)
        integer = random_randint(1,2**nbits)

        # Make sure it's odd
        integer |= 1

        # Test for primeness
        if rsa_is_prime(integer): break

        # Retry if not prime

    return integer

def rsa_are_relatively_prime(a, b):
    """Returns True if a and b are relatively prime, and False if they
    are not.

    >>> are_relatively_prime(2, 3)
    1
    >>> are_relatively_prime(2, 4)
    0
    """

    d = rsa_gcd(a, b)
    return (d == 1)

def rsa_find_p_q(nbits):
    """Returns a tuple of two different primes of nbits bits"""

    p = rsa_getprime(nbits)
    while True:
        q = rsa_getprime(nbits)
        if not q == p: break
    
    return (p, q)

def rsa_extended_euclid_gcd(a, b):
    """Returns a tuple (d, i, j) such that d = gcd(a, b) = ia + jb
    """

    if b == 0:
        return (a, 1, 0)

    q = abs(a % b)
    r = long(a / b)
    (d, k, l) = rsa_extended_euclid_gcd(b, q)

    return (d, l, k - l*r)

# Main function: calculate encryption and decryption keys
def rsa_calculate_keys(p, q, nbits):
    """Calculates an encryption and a decryption key for p and q, and
    returns them as a tuple (e, d)"""

    n = p * q
    phi_n = (p-1) * (q-1)

    while True:
        # Make sure e has enough bits so we ensure "wrapping" through
        # modulo n
        e = rsa_getprime(max(8, nbits/2))
        if rsa_are_relatively_prime(e, n) and rsa_are_relatively_prime(e, phi_n): break

    (d, i, j) = rsa_extended_euclid_gcd(e, phi_n)

    if not d == 1:
        raise Exception("e (%d) and phi_n (%d) are not relatively prime" % (e, phi_n))

    if not (e * i) % phi_n == 1:
        raise Exception("e (%d) and i (%d) are not mult. inv. modulo phi_n (%d)" % (e, i, phi_n))

    return (e, i)


def rsa_gen_keys(nbits):
    """Generate RSA keys of nbits bits. Returns (p, q, e, d).
    """

    while True:
        (p, q) = rsa_find_p_q(nbits)
        (e, d) = rsa_calculate_keys(p, q, nbits)

        # For some reason, d is sometimes negative. We don't know how
        # to fix it (yet), so we keep trying until everything is shiny
        if d > 0: break

    return (p, q, e, d)

def rsa_gen_pubpriv_keys(nbits):
    """Generates public and private keys, and returns them as (pub,
    priv).

    The public key consists of a dict {e: ..., , n: ....). The private
    key consists of a dict {d: ...., p: ...., q: ....).
    """
    
    (p, q, e, d) = rsa_gen_keys(nbits)

    return ( {'e': e, 'n': p*q}, {'d': d, 'p': p, 'q': q} )


def rsa_encrypt_int(message, ekey, n):
    """Encrypts a message using encryption key 'ekey', working modulo
    n"""

    if type(message) is int:
        return rsa_encrypt_int(long(message), ekey, n)

    if not type(message) is long:
        raise TypeError("You must pass a long or an int")

    if math_floor(math_log(message, 2)) > math_floor(math_log(n, 2)):
        raise OverflowError("The message is too long")

    return rsa_fast_exponentiation(message, ekey, n)

def rsa_decrypt_int(cyphertext, dkey, n):
    """Decrypts a cypher text using the decryption key 'dkey', working
    modulo n"""

    return rsa_encrypt_int(cyphertext, dkey, n)

def rsa_sign_int(message, dkey, n):
    """Signs 'message' using key 'dkey', working modulo n"""

    return rsa_decrypt_int(message, dkey, n)

def rsa_verify_int(signed, ekey, n):
    """verifies 'signed' using key 'ekey', working modulo n"""

    return rsa_encrypt_int(signed, ekey, n)

def rsa_picklechops(chops):
    """previously used to pickles and base64encodes it's argument chops"""

    retstring = ''
    for item in chops:
      retstring = retstring + ' ' + str(item)
    return retstring

def rsa_unpicklechops(string):
    """previously used to base64decode and unpickle it's argument string"""

    retchops = []
    for item in string.split():
      retchops.append(long(item))
    return retchops

def rsa_chopstring(message, key, n, funcref):
    """Splits 'message' into chops that are at most as long as n,
    converts these into integers, and calls funcref(integer, key, n)
    for each chop.

    Used by 'encrypt' and 'sign'.
    """

    msglen = len(message)
    nbits = int(math_floor(math_log(n, 2)))
    # JAC: subtract a byte because we're going to add an extra char on the front
    # to properly handle leading \000 bytes
    nbytes = int(nbits / 8)-1
    blocks = int(msglen / nbytes)

    if msglen % nbytes > 0:
        blocks += 1

    cypher = []
    
    for bindex in range(blocks):
        offset = bindex * nbytes
        block = message[offset:offset+nbytes]
        value = rsa_bytes2int(block)
        cypher.append(funcref(value, key, n))

    return rsa_picklechops(cypher)

def rsa_gluechops(chops, key, n, funcref):
    """Glues chops back together into a string.  calls
    funcref(integer, key, n) for each chop.

    Used by 'decrypt' and 'verify'.
    """
    message = ""

    chops = rsa_unpicklechops(chops)
    
    for cpart in chops:
        mpart = funcref(cpart, key, n)
        message += rsa_int2bytes(mpart)
    
    return message

def rsa_encrypt(message, key):
    """Encrypts a string 'message' with the public key 'key'"""
    
    return rsa_chopstring(message, key['e'], key['n'], rsa_encrypt_int)

def rsa_sign(message, key):
    """Signs a string 'message' with the private key 'key'"""
    
    return rsa_chopstring(message, key['d'], key['p']*key['q'], rsa_decrypt_int)

def rsa_decrypt(cypher, key):
    """Decrypts a cypher with the private key 'key'"""

    return rsa_gluechops(cypher, key['d'], key['p']*key['q'], rsa_decrypt_int)

def rsa_verify(cypher, key):
    """Verifies a cypher with the public key 'key'"""

    return rsa_gluechops(cypher, key['e'], key['n'], rsa_encrypt_int)


def rsa_is_valid_privatekey(key):
    """This tries to determine if a key is valid.   If it returns False, the
       key is definitely invalid.   If True, the key is almost certainly valid"""
    # must be a dict
    if type(key) is not dict:
        return False

    # missing the right keys
    if 'd' not in key or 'p' not in key or 'q' not in key:
        return False

    # has extra data in the key
    if len(key) != 3:
        return False

    for item in ['d', 'p', 'q']:
        # must have integer or long types for the key components...
        if type(key[item]) is not int and type(key[item]) is not long:
            return False

    if rsa_is_prime(key['p']) and rsa_is_prime(key['q']):
        # Seems valid...
        return True
    else:
        return False
  

def rsa_is_valid_publickey(key):
    """This tries to determine if a key is valid.   If it returns False, the
       key is definitely invalid.   If True, the key is almost certainly valid"""
    # must be a dict
    if type(key) is not dict:
        return False

    # missing the right keys
    if 'e' not in key or 'n' not in key:
        return False

    # has extra data in the key
    if len(key) != 2:
        return False

    for item in ['e', 'n']:
        # must have integer or long types for the key components...
        if type(key[item]) is not int and type(key[item]) is not long:
            return False

    if key['e'] < key['n']:
        # Seems valid...
        return True
    else:
        return False
  

def rsa_publickey_to_string(key):
  if not rsa_is_valid_publickey(key):
    raise ValueError, "Invalid public key"

  return str(key['e'])+" "+str(key['n'])


def rsa_string_to_publickey(mystr):
  if len(mystr.split()) != 2:
    raise ValueError, "Invalid public key string"

  
  return {'e':long(mystr.split()[0]), 'n':long(mystr.split()[1])}



def rsa_privatekey_to_string(key):
  if not rsa_is_valid_privatekey(key):
    raise ValueError, "Invalid private key"

  return str(key['d'])+" "+str(key['p'])+" "+str(key['q'])


def rsa_string_to_privatekey(mystr):
  if len(mystr.split()) != 3:
    raise ValueError, "Invalid private key string"

  
  return {'d':long(mystr.split()[0]), 'p':long(mystr.split()[1]), 'q':long(mystr.split()[2])}


def rsa_privatekey_to_file(key,filename):
  if not rsa_is_valid_privatekey(key):
    raise ValueError, "Invalid private key"

  fileobject = file(filename,"w")
  fileobject.write(rsa_privatekey_to_string(key))
  fileobject.close()



def rsa_file_to_privatekey(filename):
  fileobject = file(filename,'r')
  privatekeystring = fileobject.read()
  fileobject.close()

  return rsa_string_to_privatekey(privatekeystring)



def rsa_publickey_to_file(key,filename):
  if not rsa_is_valid_publickey(key):
    raise ValueError, "Invalid public key"

  fileobject = file(filename,"w")
  fileobject.write(rsa_publickey_to_string(key))
  fileobject.close()



def rsa_file_to_publickey(filename):
  fileobject = file(filename,'r')
  publickeystring = fileobject.read()
  fileobject.close()

  return rsa_string_to_publickey(publickeystring)




#end include rsa.repy
#begin include time.repy
"""
   Author: Justin Cappos

   Start Date: 8 August 2008

   Description:

   This module handles getting the time from an external source.   We get the
   remote time once and then use the offset from the local clock from then on.
"""


# Use for random sampling...
#begin include random.repy
#already included random.repy
#end include random.repy


class TimeError(Exception):
  pass


time_query_times = []

# See RFC 2030 (http://www.ietf.org/rfc/rfc2030.txt) for details about NTP

# this unpacks the data from the packet and changes it to a float
def time_convert_timestamp_to_float(timestamp):
  integerpart = (ord(timestamp[0])<<24) + (ord(timestamp[1])<<16) + (ord(timestamp[2])<<8) + (ord(timestamp[3]))
  floatpart = (ord(timestamp[4])<<24) + (ord(timestamp[5])<<16) + (ord(timestamp[6])<<8) + (ord(timestamp[7]))
  return integerpart + floatpart / float(2**32)

def time_decode_NTP_packet(ip, port, mess, ch):
  time_settime(time_convert_timestamp_to_float(mess[40:48]))
  stopcomm(ch)


# sets a remote time as the current time
#BUG: Do I need to compensate for the time taken to contact the time server
def time_settime(currenttime):
  time_query_times.append((getruntime(), currenttime))


def time_updatetime(localport):
  try:
    ip = getmyip()
  except Exception, e:
    raise TimeError, str(e)

  timeservers = ["time-a.nist.gov", "time-b.nist.gov", "time-a.timefreq.bldrdoc.gov", "time-b.timefreq.bldrdoc.gov", "time-c.timefreq.bldrdoc.gov", "utcnist.colorado.edu", "time.nist.gov", "time-nw.nist.gov", "nist1.symmetricom.com", "nist1-dc.WiTime.net", "nist1-ny.WiTime.net", "nist1-sj.WiTime.net", "nist1.aol-ca.symmetricom.com", "nist1.aol-va.symmetricom.com", "nist1.columbiacountyga.gov", "nist.expertsmi.com", "nist.netservicesgroup.com"]

  startlen = len(time_query_times)
  listenhandle = recvmess(ip,localport, time_decode_NTP_packet)

  # always close the handle before returning...
  try: 
    # try five random servers times...
    for servername in random_sample(timeservers,5):

      # this sends a request, version 3 in "client mode"
      ntp_request_string = chr(27)+chr(0)*47
      try: 
        sendmess(servername,123, ntp_request_string, ip, localport) # 123 is the NTP port
      except Exception:
        # most likely a lookup error...
        continue

      # wait for 5 seconds for a response before retrying
      for junkiterations in range(10):
        sleep(.5)

        if startlen < len(time_query_times):
          # If we've had a response, we're done!
          return
    
    
  finally:
    stopcomm(listenhandle)

  # Failure, tried servers without luck...
  raise TimeError, "Time Server update failed.  Perhaps retry later..."


def time_gettime():
  if time_query_times == []:
    raise TimeError

  # otherwise use the most recent data...
  latest_update = time_query_times[-1]

  # first item is the getruntime(), second is NTP time...
  elapsedtimesinceupdate = getruntime() - latest_update[0]

  return latest_update[1] + elapsedtimesinceupdate

# in case you want to change to time since the 1970 (as is common)
time_seconds_from_1900_to_1970 = 2208988800

#end include time.repy


# The signature for a piece of data is appended to the end and has the format:
# \n!publickey!timestamp!expirationtime!sequencedata!destination!signature
# The signature is actually the sha hash of the data (including the
# publickey, timestamp, expirationtime, sequencedata and destination) encrypted
# by the private key.



# I'll allow None and any int, long, or float (can be 0 or negative)
def signeddata_is_valid_timestamp(timestamp):
  if timestamp == None:
    return True

  if type(timestamp) is not int and type(timestamp) is not long and type(timestamp) is not float:
    return False

  return True

  
# I'll allow None and any int, long, or float that is 0 or positive
def signeddata_is_valid_expirationtime(expirationtime):
  if expirationtime == None:
    return True

  if type(expirationtime) is not int and type(expirationtime) is not long and type(expirationtime) is not float:
    return False

  if expirationtime < 0:
    return False

  return True





# sequence numbers must be 'tag:num' where tag doesn't contain ':','\n', or '!' # and num is a number
def signeddata_is_valid_sequencenumber(sequencenumber):
  if sequencenumber == None:
    return True

  if type(sequencenumber) != tuple:
    return False

  if len(sequencenumber) != 2:
    return False

  if type(sequencenumber[0]) != str:
    return False
  
  if '!' in sequencenumber[0] or ':' in sequencenumber[0] or '\n' in sequencenumber[0]:
    return False

  if type(sequencenumber[1]) != long and type(sequencenumber[1]) != int:
    return False

  return True

# Destination is an "opaque string" or None.  Should not contain a '!' or '\n'
def signeddata_is_valid_destination(destination):
  if type(destination) == type(None):
    return True

  # a string without '!' or '\n' ('!' is the separator character, '\n' is not
  # allowed anywhere in the signature)
  if type(destination) == type('abc') and '!' not in destination and '\n' not in destination:
    return True

  return False
  



def signeddata_signdata(data, privatekey, publickey, timestamp=None, expiration=None, sequenceno=None,destination=None):

# NOTE: This takes waaaay too long.   I'm going to do something simpler...
#  if not rsa_is_valid_privatekey(privatekey):
#    raise ValueError, "Invalid Private Key"
  if not privatekey:
    raise ValueError, "Invalid Private Key"
    

  if not rsa_is_valid_publickey(publickey):
    raise ValueError, "Invalid Public Key"

  if not signeddata_is_valid_timestamp(timestamp):
    raise ValueError, "Invalid Timestamp"

  if not signeddata_is_valid_expirationtime(expiration):
    raise ValueError, "Invalid Expiration Time"

  if not signeddata_is_valid_sequencenumber(sequenceno):
    raise ValueError, "Invalid Sequence Number"

  if not signeddata_is_valid_destination(destination):
    raise ValueError, "Invalid Destination"


  # Build up \n!pubkey!timestamp!expire!sequence!dest!signature
  totaldata = data + "\n!"+rsa_publickey_to_string(publickey)
  totaldata = totaldata+"!"+signeddata_timestamp_to_string(timestamp)
  totaldata = totaldata+"!"+signeddata_expiration_to_string(expiration)
  totaldata = totaldata+"!"+signeddata_sequencenumber_to_string(sequenceno)
  totaldata = totaldata+"!"+signeddata_destination_to_string(destination)
  
  # Time to get the hash...
  shahashobj = sha()
  shahashobj.update(totaldata)
  hashdata = shahashobj.digest()


  # ...and sign it
  signature = rsa_sign(hashdata, privatekey)

  totaldata = totaldata+"!"+str(signature)

  return totaldata


# return [original data, signature]
def signeddata_split_signature(data):
  return data.rsplit('\n',1)


# checks the signature.   If the public key is specified it must match that in
# the file...
def signeddata_issignedcorrectly(data, publickey=None):
  # I'll check signature over all of thesigneddata
  thesigneddata, signature = data.rsplit('!',1)
  junk, rawpublickey, junktimestamp, junkexpiration, junksequenceno, junkdestination = thesigneddata.rsplit('!',5)
  
  if publickey != None and rsa_string_to_publickey(rawpublickey) != publickey:
    return False

  publickey = rsa_string_to_publickey(rawpublickey)

  try: 
    # extract the hash from the signature
    signedhash = rsa_verify(signature, publickey)
  except TypeError, e:
    if 'RSA' not in str(e):
      raise
    # Bad signature or public key
    return False

  # Does the hash match the signed data?
  if signedhash == sha_hash(thesigneddata):
    return True
  else:
    return False
  

def signeddata_string_to_destination(destination):
  if destination == 'None':
    return None
  return destination

def signeddata_destination_to_string(destination):
  return str(destination)


def signeddata_string_to_timestamp(rawtimestamp):
  if rawtimestamp == 'None':
    return None
  return float(rawtimestamp)


def signeddata_timestamp_to_string(timestamp):
  return str(timestamp)

def signeddata_string_to_expiration(rawexpiration):
  if rawexpiration == 'None':
    return None
  return float(rawexpiration)

def signeddata_expiration_to_string(expiration):
  return str(expiration)



def signeddata_string_to_sequencenumber(sequencenumberstr):
  if sequencenumberstr == 'None' or sequencenumberstr == None:
    return None

  if type(sequencenumberstr) is not str:
    raise ValueError, "Invalid sequence number type '"+str(type(sequencenumberstr))+"' (must be string)"
    
  if len(sequencenumberstr.split(':')) != 2:
    raise ValueError, "Invalid sequence number string (does not contain 1 ':')"

  if '!' in sequencenumberstr:
    raise ValueError, "Invalid sequence number data: '!' not allowed"
  
  return sequencenumberstr.split(':')[0],int(sequencenumberstr.split(':')[1])


def signeddata_sequencenumber_to_string(sequencenumber):
  if type(sequencenumber) is type(None):
    return 'None'

  if type(sequencenumber[0]) is not str:
    raise ValueError, "Invalid sequence number type"

  if type(sequencenumber[1]) is not long and type(sequencenumber[1]) is not int:
    raise ValueError, "Invalid sequence number count type"
    
  if len(sequencenumber) != 2:
    raise ValueError, "Invalid sequence number"

  return sequencenumber[0]+":"+str(sequencenumber[1])


def signeddata_iscurrent(expiretime):
  if expiretime == None:
    return True

  # may throw TimeError...
  currenttime = time_gettime()
  if expiretime > currenttime:
    return True
  else:
    return False




def signeddata_has_good_sequence_transition(oldsequence, newsequence):
  # None is always allowed by any prior sequence
  if newsequence == None:
    return True

  if oldsequence == None: 
    # is this the start of a sequence when there was none prior?
    if newsequence[1] == 0:
      return True
    return False

  # They are from the same sequence
  if oldsequence[0] == newsequence[0]:
    # and this must be the next number to be valid
    if oldsequence[1] + 1 == newsequence[1]:
      return True
    return False

  else: 
    # Different sequences
 
    # is this the start of a new sequence?
    if newsequence[1] == 0:
      return True

    # otherwise this isn't good
    return False


# used in lieu of a global for destination checking
signeddata_identity = {}

# Used to set identity for destination checking...
def signeddata_set_identity(identity):
  signeddata_identity['me'] = identity


def signeddata_destined_for_me(destination):
  # None means it's for everyone
  if destination == None:
    return True

  # My identity wasn't set and the destination was, so fail...
  if 'me' not in signeddata_identity:
    return False

  # otherwise, am I in the colon delimited list?
  if signeddata_identity['me'] in destination.split(':'):
    return True
  return False



def signeddata_split(data):
  originaldata, rawpublickey, rawtimestamp, rawexpiration, rawsequenceno,rawdestination, junksignature = data.rsplit('!',6)
  
  # strip the '\n' off of the original data...
  return originaldata[:-1], rsa_string_to_publickey(rawpublickey), signeddata_string_to_timestamp(rawtimestamp), signeddata_string_to_expiration(rawexpiration), signeddata_string_to_sequencenumber(rawsequenceno), signeddata_string_to_destination(rawdestination)



def signeddata_getcomments(signeddata, publickey=None):
  """Returns a list of problems with the signed data (but doesn't look at sequence number or timestamp data)."""
  returned_comments = []

  try:
    junkdata, pubkey, timestamp, expiretime, sequenceno, destination = signeddata_split(signeddata)
  except KeyError:
    return ['Malformed signed data']

  if publickey != None and publickey != pubkey:
    returned_comments.append('Different public key')

  if not signeddata_issignedcorrectly(signeddata, publickey):
    returned_comments.append("Bad signature")
  
  try:
    if not signeddata_iscurrent(expiretime):
      returned_comments.append("Expired signature")
  except TimeError:
    returned_comments.append("Cannot check expiration")

  if destination != None and not signeddata_destined_for_me(destination):
    returned_comments.append("Not destined for this node")

  return returned_comments



signeddata_warning_comments = [ 'Timestamps match', "Cannot check expiration" ]
signeddata_fatal_comments = ['Malformed signed data', 'Different public key', "Bad signature", "Expired signature", 'Public keys do not match', 'Invalid sequence transition', 'Timestamps out of order', 'Not destined for this node']

signeddata_all_comments = signeddata_warning_comments + signeddata_fatal_comments


def signeddata_shouldtrust(oldsigneddata, newsigneddata, publickey=None):
  """ Returns False for 'don't trust', None for 'use your discretion' and True 
  for everything is okay.   The second item in the return value is a list of
  reasons / justifications"""

  returned_comments = []

# we likely only want to keep the signature data around in many cases.   For 
# example, if the request is huge.   
#  if not signeddata_issignedcorrectly(oldsigneddata, publickey):
#    raise ValueError, "Old signed data is not correctly signed!"

  if not signeddata_issignedcorrectly(newsigneddata, publickey):
    returned_comments.append("Bad signature")
    return False, returned_comments
    
  # extract information about the signatures
  oldjunk, oldpubkey, oldtime, oldexpire, oldsequence, olddestination = signeddata_split(oldsigneddata)
  newjunk, newpubkey, newtime, newexpire, newsequence, newdestination = signeddata_split(newsigneddata)
    
  if oldpubkey != newpubkey:
    returned_comments.append('Public keys do not match')
    # fall through and reject below

  # get comments on everything but the timestamp and sequence number
  returned_comments = returned_comments + signeddata_getcomments(newsigneddata, publickey)
  
  # check the sequence number data...
  if not signeddata_has_good_sequence_transition(oldsequence, newsequence):
    returned_comments.append('Invalid sequence transition')

  # check the timestamps...  
  if (newtime == None and oldtime != None) or oldtime == None or oldtime > newtime:
    # if the timestamps are reversed (None is the earliest possible)
    returned_comments.append('Timestamps out of order')
  elif oldtime != None and newtime != None and oldtime == newtime:
    # the timestamps are equal but not none...
    returned_comments.append('Timestamps match')
  else:   # So they either must both be None or oldtime < newtime
    assert((newtime == oldtime == None) or oldtime < newtime)
  

  # let's see what happened...
  if returned_comments == []:
    return True, []
  for comment in returned_comments:
    if comment in signeddata_fatal_comments:
      return False, returned_comments

    # if not a failure, should be a warning comment
    assert(comment in signeddata_warning_comments)

  # Warnings, so I won't return True
  return None, returned_comments
  
#end include signeddata.repy

# session wrapper (breaks the stream into messages)
# an abstracted "itemized data communication" in a separate API
#begin include session.repy
# This module wraps communications in a signaling protocol.   The purpose is to
# overlay a connection-based protocol with explicit message signaling.   
#
# The protocol is to send the size of the message followed by \n and then the
# message itself.   The size of a message must be able to be stored in 
# sessionmaxdigits.   A size of -1 indicates that this side of the connection
# should be considered closed.
#
# Note that the client will block while sending a message, and the receiver 
# will block while recieving a message.   
#
# While it should be possible to reuse the connectionbased socket for other 
# tasks so long as it does not overlap with the time periods when messages are 
# being sent, this is inadvisable.

class SessionEOF(Exception):
  pass

sessionmaxdigits = 20

# get the next message off of the socket...
def session_recvmessage(socketobj):

  messagesizestring = ''
  # first, read the number of characters...
  for junkcount in range(sessionmaxdigits):
    currentbyte = socketobj.recv(1)

    if currentbyte == '\n':
      break
    
    # not a valid digit
    if currentbyte not in '0123456789' and messagesizestring != '' and currentbyte != '-':
      raise ValueError, "Bad message size"
     
    messagesizestring = messagesizestring + currentbyte

  else:
    # too large
    raise ValueError, "Bad message size"

  messagesize = int(messagesizestring)
  
  # nothing to read...
  if messagesize == 0:
    return ''

  # end of messages
  if messagesize == -1:
    raise SessionEOF, "Connection Closed"

  if messagesize < 0:
    raise ValueError, "Bad message size"

  data = ''
  while len(data) < messagesize:
    chunk =  socketobj.recv(messagesize-len(data))
    if chunk == '': 
      raise SessionEOF, "Connection Closed"
    data = data + chunk

  return data

# a private helper function
def session_sendhelper(socketobj,data):
  sentlength = 0
  # if I'm still missing some, continue to send (I could have used sendall
  # instead but this isn't supported in repy currently)
  while sentlength < len(data):
    thissent = socketobj.send(data[sentlength:])
    sentlength = sentlength + thissent



# send the message 
def session_sendmessage(socketobj,data):
  header = str(len(data)) + '\n'
  session_sendhelper(socketobj,header)

  session_sendhelper(socketobj,data)



#end include session.repy


# The idea is that this module returns "node manager handles".   A handle
# may be used to communicate with a node manager and issue commands.   If the
# caller wants to have a set of node managers with the same state, this can
# be done by something like:
#
#
# myid =    # some unique, non-repeating value
# nmhandles = []
# for nm in nodemanagers:
#   nmhandles.append(nmclient_createhandle(nm, sequenceid = myid))
#
# 
# def do_action(action):
#   for nmhandle in nmhandles:
#     nmclient_doaction(nmhandle, ... )
#
#
# The above code snippet will ensure that none of the nmhandles perform the
# actions called in do_action() out of order.   A node that "misses" an action
# (perhaps due to a network or node failure) will not perform later actions 
# unless the sequenceid is reset.
#
# Note that the above calls to nmclient_createhandle and nmclient_doaction 
# should really be wrapped in try except blocks for NMClientExceptions



# Thrown when a failure occurs when trying to communicate with a node
class NMClientException(Exception):
  pass

# This holds all of the client handles.   A client handle is merely a 
# string that is the key to this dict.   All of the information is stored in
# the dictionary value (a dict with keys for IP, port, sessionID, timestamp,
# identity, expirationtime, public key, private key, and vesselID).   
nmclient_handledict = {}

# BUG: How do I do this and have it be portable across repy <-> python?
# needed when assigning new handles to prevent race conditions...
nmclient_handledictlock = getlock()



# Note: I open a new connection for every request.   Is this really what I want
# to do?   It seemed easiest but likely has performance implications

# Sends data to a node (opens the connection, writes the 
# communication header, sends all the data, receives the result, and returns
# the result)...
def nmclient_rawcommunicate(nmhandle, *args):

  try:
    thisconnobject = openconn(nmclient_handledict[nmhandle]['IP'], nmclient_handledict[nmhandle]['port']) 
  except Exception, e:
    raise NMClientException, str(e)

  # always close the connobject
  try:

    # send the args separated by '|' chars (as is expected by the node manager)
    session_sendmessage(thisconnobject, '|'.join(args))
    return session_recvmessage(thisconnobject)
  finally:
    thisconnobject.close()




# Sends data to a node (opens the connection, writes the 
# communication header, sends all the data, receives the result, and returns
# the result)...
def nmclient_signedcommunicate(nmhandle, *args):

  # need to check lots of the nmhandle settings...

  if nmclient_handledict[nmhandle]['timestamp'] == True:
    # set the time based upon the current time...
    timestamp = time_gettime()
  elif not nmclient_handledict[nmhandle]['timestamp']:
    # we're false, so set to None
    timestamp = None
  else:
    # For some reason, the caller wanted a specific time...
    timestamp = nmclient_handledict[nmhandle]['timestamp']

  if nmclient_handledict[nmhandle]['publickey']:
    publickey = nmclient_handledict[nmhandle]['publickey']
  else:
    raise NMClientException, "Must have public key for signed communication"

  if nmclient_handledict[nmhandle]['privatekey']:
    privatekey = nmclient_handledict[nmhandle]['privatekey']
  else:
    raise NMClientException, "Must have private key for signed communication"

  # use this blindly (None or a value are both okay)
  sequenceid = nmclient_handledict[nmhandle]['sequenceid']

  if nmclient_handledict[nmhandle]['expiration']:
    if timestamp == None:
      # highly dubious.   However, it's technically valid, so let's allow it.
      expirationtime = nmclient_handledict[nmhandle]['expiration']
    else:
      expirationtime = timestamp + nmclient_handledict[nmhandle]['expiration']

  else:
    # they don't want this to expire
    expirationtime = nmclient_handledict[nmhandle]['expiration']


  # use this blindly (None or a value are both okay)
  identity = nmclient_handledict[nmhandle]['identity']


  # build the data to send.   Ideally we'd do: datatosend = '|'.join(args)
  # we can't do this because some args may be non-strings...
  datatosend = args[0]
  for arg in args[1:]:
    datatosend = datatosend + '|' + str(arg)
    

  try:
    thisconnobject = openconn(nmclient_handledict[nmhandle]['IP'], nmclient_handledict[nmhandle]['port']) 
  except Exception, e:
    raise NMClientException, str(e)

  # always close the connobject afterwards...
  try:
    try:
      signeddata = signeddata_signdata(datatosend, privatekey, publickey, timestamp, expirationtime, sequenceid, identity)
    except ValueError, e:
      raise NMClientException, str(e)
    session_sendmessage(thisconnobject, signeddata)
    message = session_recvmessage(thisconnobject)
    return message
  finally:
    thisconnobject.close()



def nmclient_safelygethandle():
  # I lock to prevent a race when adding handles to the dictionary.   I don't
  # need a lock when removing because a race is benign (it prevents reuse)
  nmclient_handledictlock.acquire()
  try:
    potentialhandle = randomfloat()
    while potentialhandle in nmclient_handledict:
      potentialhandle = randomfloat()
    return potentialhandle
  finally:
    nmclient_handledictlock.release()





# Create a new handle, the IP, port must be provided but others are optional.
# The default is to have no sequenceID, timestamps on, expiration time of 1 
# hour, and the program should set and use the identity of the node.   The 
# public key, private key, and vesselids are left uninitialized unless 
# specified elsewhere.   Regardless, the keys and vesselid are not used to 
# create the handle and so are merely transfered to the created handle.
def nmclient_createhandle(nmIP, nmport, sequenceid = None, timestamp=True, identity = True, expirationtime = 60*60, publickey = None, privatekey = None, vesselid = None):

  thisentry = {}

  thisentry['IP'] = nmIP
  thisentry['port'] = nmport
  thisentry['sequenceid'] = sequenceid
  thisentry['timestamp'] = timestamp
  thisentry['expiration'] = expirationtime
  thisentry['publickey'] = publickey
  thisentry['privatekey'] = privatekey
  thisentry['vesselid'] = vesselid

    
  newhandle = nmclient_safelygethandle()

  nmclient_handledict[newhandle] = thisentry

  # Use GetVessels as a "hello" test (and for identity reasons as shown below)
  try:
    response = nmclient_rawsay(newhandle, 'GetVessels')

  except (ValueError, NMClientException, KeyError), e:
    del nmclient_handledict[newhandle]
    raise NMClientException, e


  # set up the identity
  if identity == True:
    for line in response.split('\n'):
      if line.startswith('Nodekey: '):
        # get everything after the Nodekey as the identity
        nmclient_handledict[newhandle]['identity'] = line[len('Nodekey: '):]
        break
        
    else:
      raise NMClientException, "Do not understand node manager identity in identification"

  else:
    nmclient_handledict[newhandle]['identity'] = identity

  # it worked!
  return newhandle



def nmclient_duplicatehandle(nmhandle):
  newhandle = nmclient_safelygethandle()
  nmclient_handledict[newhandle] = nmclient_handledict[nmhandle].copy()
  return newhandle

# public.   Use this to clean up a handle
def nmclient_destroyhandle(nmhandle):
  try:
    del nmclient_handledict[nmhandle]
  except KeyError:
    return False
  return True
  

# public.   Use these to get / set attributes about the handles...
def nmclient_get_handle_info(nmhandle):
  return nmclient_handledict[nmhandle].copy()


def nmclient_set_handle_info(nmhandle, dict):
  nmclient_handledict[nmhandle] = dict


  

# Public:  Use this for non-signed operations...
def nmclient_rawsay(nmhandle, *args):
  fullresponse = nmclient_rawcommunicate(nmhandle, *args)

  try:
    (response, status) = fullresponse.rsplit('\n',1)
  except KeyError:
    raise NMClientException, "Communication error '"+fullresponse+"'"

  if status == 'Success':
    return response
  elif status == 'Error':
    raise NMClientException, "Node Manager error '"+response+"'"
  elif status == 'Warning':
    raise NMClientException, "Node Manager warning '"+response+"'"
  else:
    raise NMClientException, "Unknown status '"+fullresponse+"'"
  



# Public:  Use this for signed operations...
def nmclient_signedsay(nmhandle, *args):
  fullresponse = nmclient_signedcommunicate(nmhandle, *args)

  try:
    (response, status) = fullresponse.rsplit('\n',1)
  except KeyError:
    raise NMClientException, "Communication error '"+fullresponse+"'"

  if status == 'Success':
    return response
  elif status == 'Error':
    raise NMClientException, "Node Manager error '"+response+"'"
  elif status == 'Warning':
    raise NMClientException, "Node Manager warning '"+response+"'"
  else:
    raise NMClientException, "Unknown status '"+fullresponse+"'"
  


# public, use this to do raw communication with a vessel
def nmclient_rawsaytovessel(nmhandle, call, *args):
  vesselid = nmclient_handledict[nmhandle]['vesselid']
  if not vesselid:
    raise NMClientException, "Must set vesselid to communicate with a vessel"

  return nmclient_rawsay(nmhandle,call, vesselid,*args)
  


# public, use this to do a signed communication with a vessel
def nmclient_signedsaytovessel(nmhandle, call, *args):
  vesselid = nmclient_handledict[nmhandle]['vesselid']
  if not vesselid:
    raise NMClientException, "Must set vesselid to communicate with a vessel"

  return nmclient_signedsay(nmhandle,call, vesselid,*args)


# public, lists the vessels that the provided key owns or can use
def nmclient_listaccessiblevessels(nmhandle, publickey):

  vesselinfo = nmclient_getvesseldict(nmhandle)

  # these will be filled with relevant vessel names...
  ownervessels = []
  uservessels = []

  for vesselname in vesselinfo['vessels']:
    if publickey == vesselinfo['vessels'][vesselname]['ownerkey']:
      ownervessels.append(vesselname)

    if 'userkeys' in vesselinfo['vessels'][vesselname] and publickey in vesselinfo['vessels'][vesselname]['userkeys']:
      uservessels.append(vesselname)


  return (ownervessels, uservessels)



#public, parse a node manager's vessel information and return it to the user...
def nmclient_getvesseldict(nmhandle):

  response = nmclient_rawsay(nmhandle, 'GetVessels')

  retdict = {}
  retdict['vessels'] = {}

  # here we loop through the response and set the dicts as appropriate
  lastvesselname = None
  for line in response.split('\n'):
    if not line:
      # empty line.   Let's allow it...
      pass
    elif line.startswith('Version: '):
      retdict['version'] = line[len('Version: '):]
    elif line.startswith('Nodename: '):
      retdict['nodename'] = line[len('Nodename: '):]
    elif line.startswith('Nodekey: '):
      retdict['nodekey'] = rsa_string_to_publickey(line[len('Nodekey: '):])
 
    # start of a vessel
    elif line.startswith('Name: '):
      # if there is a previous vessel write it to the dict...
      if lastvesselname:
        retdict['vessels'][lastvesselname] = thisvessel

      thisvessel = {}
      # NOTE:I'm changing this so that userkeys will always exist even if there
      # are no user keys (in this case it has an empty list).   I think this is
      # the right functionality.
      thisvessel['userkeys'] = []
      lastvesselname = line[len('Name: '):]

    elif line.startswith('OwnerKey: '):
      thiskeystring = line[len('OwnerKey: '):]
      thiskey = rsa_string_to_publickey(thiskeystring)
      thisvessel['ownerkey'] = thiskey

    elif line.startswith('OwnerInfo: '):
      thisownerstring = line[len('OwnerInfo: '):]
      thisvessel['ownerinfo'] = thisownerstring

    elif line.startswith('Status: '):
      thisstatus = line[len('Status: '):]
      thisvessel['status'] = thisstatus

    elif line.startswith('Advertise: '):
      thisadvertise = line[len('Advertise: '):]
      if thisadvertise == 'True':
        thisvessel['advertise'] = True
      elif thisadvertise == 'False':
        thisvessel['advertise'] = False
      else:
        raise NMClientException, "Unknown advertise type '"+thisadvertise+"'"

    elif line.startswith('UserKey: '):
      thiskeystring = line[len('UserKey: '):]
      thiskey = rsa_string_to_publickey(thiskeystring)

      thisvessel['userkeys'].append(thiskey)

    else:
      raise NMClientException, "Unknown line in GetVessels response '"+line+"'"


  if lastvesselname:
    retdict['vessels'][lastvesselname] = thisvessel
  return retdict
#end include nmclient.repy

#begin include time.repy
#already included time.repy
#end include time.repy

#begin include rsa.repy
#already included rsa.repy
#end include rsa.repy

#begin include listops.repy
""" 
Author: Justin Cappos

Module: A simple library of list commands that allow the programmer
        to do list composition operations

Start date: November 11th, 2008

This is a really simple module, only broken out to avoid duplicating 
functionality.

This was adopted from previous code in seash.   

I really should be using sets instead I think.   These are merely for 
convenience when you already have lists.

"""


def listops_difference(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in list_a that are not in list_b
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a - list_b
  """

  retlist = []
  for item in list_a:
    if item not in list_b:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)


def listops_union(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in list_a or in list_b.   
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a union list_b
  """

  retlist = list_a[:]
  for item in list_b: 
    if item not in list_a:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)


def listops_intersect(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in both list_a and list_b.   
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a intersect list_b
  """

  retlist = []
  for item in list_a:
    if item in list_b:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)
      

def listops_uniq(list_a):
  """
   <Purpose>
      Return a list that has no duplicate items

   <Arguments>
      list_a
        The list to operate on

   <Exceptions>
      TypeError if list_a is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing the unique items in list_a
  """
  retlist = []
  for item in list_a:
    if item not in retlist:
      retlist.append(item)

  return retlist


#end include listops.repy

#begin include parallelize.repy
""" 
Author: Justin Cappos

Module: A parallelization module.   It performs actions in parallel to make it
        easy for a user to call a function with a list of tasks.

Start date: November 11th, 2008

This module is adapted from code in seash which had similar functionality.

NOTE (for the programmer using this module).   It's really important to 
write concurrency safe code for the functions they provide us.  It will not 
work to write:

def foo(...):
  mycontext['count'] = mycontext['count'] + 1

YOU MUST PUT A LOCK AROUND SUCH ACCESSES.

"""


# I use this to get unique identifiers. 
#begin include uniqueid.repy
""" 
Author: Justin Cappos

Module: A simple library that provides a unique ID for each call

Start date: November 11th, 2008

This is a really, really simple module, only broken out to avoid duplicating 
functionality.

NOTE: This will give unique ids PER FILE.   If you have multiple python 
modules that include this, they will have the potential to generate the
same ID.

"""

# This is a list to prevent using part of the user's mycontext dict
uniqueid_idlist = [0]
uniqueid_idlock = getlock()

def uniqueid_getid():
  """
   <Purpose>
      Return a unique ID in a threadsafe way

   <Arguments>
      None

   <Exceptions>
      None

   <Side Effects>
      None.

   <Returns>
      The ID (an integer)
  """

  uniqueid_idlock.acquire()

  # I'm using a list because I need a global, but don't want to use the 
  # programmer's dict
  myid = uniqueid_idlist[0]
  uniqueid_idlist[0] = uniqueid_idlist[0] + 1

  uniqueid_idlock.release()

  return myid


def listops_union(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in list_a or in list_b.   
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a union list_b
  """

  retlist = list_a[:]
  for item in list_b: 
    if item not in list_a:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)


def listops_intersect(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in both list_a and list_b.   
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a intersect list_b
  """

  retlist = []
  for item in list_a:
    if item in list_b:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)
      

def listops_uniq(list_a):
  """
   <Purpose>
      Return a list that has no duplicate items

   <Arguments>
      list_a
        The list to operate on

   <Exceptions>
      TypeError if list_a is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing the unique items in list_a
  """
  retlist = []
  for item in list_a:
    if item not in retlist:
      retlist.append(item)

  return retlist


#end include uniqueid.repy



class ParallelizeError(Exception):
  """An error occurred when operating on a parallelized task"""


# This has information about all of the different parallel functions.
# The keys are unique integers and the entries look like this:
# {'abort':False, 'callfunc':callfunc, 'callargs':callargs,
# 'targetlist':targetlist, 'availabletargetpositions':positionlist,
# 'runninglist':runninglist, 'result':result}
#
# abort is used to determine if future events should be aborted.
# callfunc is the function to call
# callargs are extra arguments to pass to the function
# targetlist is the list of items to call the function with
# runninglist is used to track which events are executing
# result is a dictionary that contains information about completed function.
#    The format of result is:
#      {'exception':list of tuples with (target, exception string), 
#       'aborted':list of targets,
#       'returned':list of tuples with (target, return value)}
# 
parallelize_info_dict = {}



def parallelize_closefunction(parallelizehandle):
  """
   <Purpose>
      Clean up the state created after calling parallelize_initfunction.

   <Arguments>
      parallelizehandle:
         The handle returned by parallelize_initfunction
          

   <Exceptions>
      None

   <Side Effects>
      Will try to abort future functions if possible

   <Returns>
      True if the parallelizehandle was recognized or False if the handle is
      invalid or already closed.
  """

  # There is no sense trying to check then delete, since there may be a race 
  # with multiple calls to this function.
  try:
    del parallelize_info_dict[parallelizehandle]
  except KeyError:
    return False
  else:
    return True

    



def parallelize_abortfunction(parallelizehandle):
  """
   <Purpose>
      Cause pending events for a function to abort.   Events will finish 
      processing their current event.

   <Arguments>
      parallelizehandle:
         The handle returned by parallelize_initfunction
          

   <Exceptions>
      ParallelizeException is raised if the handle is unrecognized

   <Side Effects>
      None

   <Returns>
      True if the function was not previously aborting and is now, or False if 
      the function was already set to abort before the call.
  """

  
  try:
    if parallelize_info_dict[parallelizehandle]['abort'] == False:
      parallelize_info_dict[parallelizehandle]['abort'] = True
      return True
    else:
      return False
  except KeyError:
    raise ParallelizeException("Cannot abort the parallel execution of a non-existent handle:"+str(parallelizehandle))



def parallelize_isfunctionfinished(parallelizehandle):
  """
   <Purpose>
      Indicate if a function is finished

   <Arguments>
      parallelizehandle:
         The handle returned by parallelize_initfunction
          

   <Exceptions>
      ParallelizeException is raised if the handle is unrecognized

   <Side Effects>
      None

   <Returns>
      True if the function has finished, False if it is still has events running
  """

  
  try:
    if parallelize_info_dict[parallelizehandle]['runninglist']:
      return False
    else:
      return True
  except KeyError:
    raise ParallelizeException("Cannot get status for the parallel execution of a non-existent handle:"+str(parallelizehandle))





def parallelize_getresults(parallelizehandle):
  """
   <Purpose>
      Get information about a parallelized function

   <Arguments>
      parallelizehandle:
         The handle returned by parallelize_initfunction
          
   <Exceptions>
      ParallelizeException is raised if the handle is unrecognized

   <Side Effects>
      None

   <Returns>
      A dictionary with the results.   The format is
        {'exception':list of tuples with (target, exception string), 
         'aborted':list of targets, 'returned':list of tuples with (target, 
         return value)}
  """

  
  try:
    # I copy so that the user doesn't have to deal with the fact I may still
    # be modifying it
    return parallelize_info_dict[parallelizehandle]['result'].copy()
  except KeyError:
    raise ParallelizeException("Cannot get results for the parallel execution of a non-existent handle:"+str(parallelizehandle))



      



      


def parallelize_initfunction(targetlist, callerfunc,concurrentevents=5, *extrafuncargs):
  """
   <Purpose>
      Call a function with each argument in a list in parallel

   <Arguments>
      targetlist:
          The list of arguments the function should be called with.   Each
          argument is passed once to the function.   Items may appear in the
          list multiple times

      callerfunc:
          The function to call
 
      concurrentevents:
          The number of events to issue concurrently (default 5).   No more 
          than len(targetlist) events will be concurrently started.

      extrafuncargs:
          Extra arguments the function should be called with (every function
          is passed the same extra args).

   <Exceptions>
      ParallelizeException is raised if there isn't at least one free event.   
      However, if there aren't at least concurrentevents number of free events,
      this is not an error (instead this is reflected in parallelize_getstatus)
      in the status information.

   <Side Effects>
      Starts events, etc.

   <Returns>
      A handle used for status information, etc.
  """

  parallelizehandle = uniqueid_getid()

  # set up the dict locally one line at a time to avoid a ginormous line
  handleinfo = {}
  handleinfo['abort'] = False
  handleinfo['callfunc'] = callerfunc
  handleinfo['callargs'] = extrafuncargs
  # make a copy of target list because 
  handleinfo['targetlist'] = targetlist[:]
  handleinfo['availabletargetpositions'] = range(len(handleinfo['targetlist']))
  handleinfo['result'] = {'exception':[],'returned':[],'aborted':[]}
  handleinfo['runninglist'] = []

  
  parallelize_info_dict[parallelizehandle] = handleinfo

  # don't start more threads than there are targets (duh!)
  threads_to_start = min(concurrentevents, len(handleinfo['targetlist']))

  for workercount in range(threads_to_start):
    # we need to append the workercount here because we can't return until 
    # this is scheduled without having race conditions
    parallelize_info_dict[parallelizehandle]['runninglist'].append(workercount)
    try:
      settimer(0.0, parallelize_execute_function, (parallelizehandle,workercount))
    except:
      # If I'm out of resources, stop
      # remove this worker (they didn't start)
      parallelize_info_dict[parallelizehandle]['runninglist'].remove(workercount)
      if not parallelize_info_dict[parallelizehandle]['runninglist']:
        parallelize_closefunction(parallelizehandle)
        raise Exception, "No events available!"
      break
  
  return parallelizehandle
    


def parallelize_execute_function(handle, myid):
  # This is internal only.   It's used to execute the user function...

  # No matter what, an exception in me should not propagate up!   Otherwise,
  # we might result in the program's termination!
  try:

    while True:
      # separate this from below functionality to minimize scope of try block
      thetargetlist = parallelize_info_dict[handle]['targetlist']
      try:
        mytarget = thetargetlist.pop()
      except IndexError:
        # all items are gone, let's return
        return

      # if they want us to abort, put this in the aborted list
      if parallelize_info_dict[handle]['abort']:
        parallelize_info_dict[handle]['result']['aborted'].append(mytarget)

      else:
        # otherwise process this normally

        # limit the scope of the below try block...
        callfunc = parallelize_info_dict[handle]['callfunc']
        callargs = parallelize_info_dict[handle]['callargs']

        try:
          retvalue = callfunc(mytarget,*callargs)
        except Exception, e:
          # always log on error.   We need to report what happened
          parallelize_info_dict[handle]['result']['exception'].append((mytarget,str(e)))
        else:
          # success, add it to the dict...
          parallelize_info_dict[handle]['result']['returned'].append((mytarget,retvalue))


  except KeyError:
    # A KeyError is normal if they've closed the handle
    return

  except Exception, e:
    print 'Internal Error: Exception in parallelize_execute_function',e

  finally:
    # remove my entry from the list of running worker threads...
    try:
      parallelize_info_dict[handle]['runninglist'].remove(myid)
    except ValueError:
      pass
    

    

#end include parallelize.repy

import traceback

import advertise            #  used to do OpenDHT lookups








#### Helper functions and exception definitions


  
# Use this to signal an error we want to print...
class UserError(Exception):
  """This indicates the user typed an incorrect command"""







def is_immutable_targetname(targetname):
  if targetname.startswith('%') or ':' in targetname:
    return True
  return False


def valid_targetname(targetname):
  if targetname.startswith('%') or ':' in targetname or ' ' in targetname:
    return False
  return True


def fit_string(stringdata, length):
  if len(stringdata) > length:
    return stringdata[:length-3]+'...'
  return stringdata


nextidlock = getlock()
def atomically_get_nextid():
  global nextid

  # mutex around getting an id
  nextidlock.acquire()

  myid = nextid
  nextid = nextid + 1

  nextidlock.release()

  return myid
    
  

# adds a vessel and returns the new ID...
def add_vessel(longname, keyname, vesselhandle):
  vesselinfo[longname] = {}
  vesselinfo[longname]['handle'] = vesselhandle
  vesselinfo[longname]['keyname'] = keyname
  vesselinfo[longname]['IP'] = longname.split(':')[0]
  vesselinfo[longname]['port'] = int(longname.split(':')[1])
  vesselinfo[longname]['vesselname'] = longname.split(':')[2]
  
  # set up a reference to myself...
  targets[longname] = [longname]

  myid = atomically_get_nextid()

  # add my id...
  targets['%'+str(myid)] = [longname]
  vesselinfo[longname]['ID'] = '%'+str(myid)

  # add me to %all...
  targets['%all'].append(longname)

  return myid




def copy_vessel(longname, newvesselname):
  newhandle = nmclient_duplicatehandle(vesselinfo[longname]['handle'])
  newlongname = vesselinfo[longname]['IP']+":"+str(vesselinfo[longname]['port'])+":"+newvesselname
  add_vessel(newlongname,vesselinfo[longname]['keyname'],newhandle)
  return newlongname

def delete_vessel(longname):
  # remove the item...
  del vesselinfo[longname]

  # remove the targets that reference it...
  for target in targets.copy():
    # if in my list...
    if longname in targets[target]:
      # if this is the %num entry or longname entry...
      if ('%' in target and target != '%all') or longname == target:
        del targets[target]
        continue
      # otherwise remove the item from the list...
      targets[target].remove(longname)



def longnamelist_to_nodelist(longnamelist):
  
  retlist = []
  for longname in longnamelist:
    nodename = vesselinfo[longname]['IP']+":"+str(vesselinfo[longname]['port'])
    retlist.append(nodename)

  return retlist


def find_handle_for_node(nodename):
  
  for longname in vesselinfo:
    if longname.rsplit(':',1)[0] == nodename:
      return vesselinfo[longname]['handle']
  raise IndexError("Cannot find handle for '"+nodename+"'")





#################### functions that operate on a target

MAX_CONTACT_WORKER_THREAD_COUNT = 10


# This function abstracts out contacting different nodes.   It spawns off 
# multiple worker threads to handle the clients...
# by a threaded model in the future...
# NOTE: entries in targetlist are assumed by me to be unique
def contact_targets(targetlist, func,*args):
  
  phandle = parallelize_initfunction(targetlist, func, MAX_CONTACT_WORKER_THREAD_COUNT, *args)

  while not parallelize_isfunctionfinished(phandle):
    sleep(.1)
  
  # I'm going to change the format slightly...
  resultdict = parallelize_getresults(phandle)

  # There really shouldn't be any exceptions in any of the routines...
  if resultdict['exception']:
    print "WARNING: ",resultdict['exception']

  # I'm going to convert the format to be targetname (as the key) and 
  # a value with the return value...
  retdict = {}
  for nameandretval in resultdict['returned']:
    retdict[nameandretval[0]] = nameandretval[1]

  return retdict
    

    

# This function abstracts out contacting different nodes.   It is obsoleted by
# the threaded model...   This code is retained for testing reasons only
def simple_contact_targets(targetlist, func,*args):
  retdict = {}

  # do the function on each target, returning a dict of results.
  for target in targetlist:
    retdict[target] = func(target,*args)

  return retdict
    






# used in show log
def showlog_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    logdata = nmclient_signedsay(vesselinfo[longname]['handle'],"ReadVesselLog",vesselname)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, logdata)





# used in show resources
def showresources_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    resourcedata = nmclient_rawsay(vesselinfo[longname]['handle'],"GetVesselResources",vesselname)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, resourcedata)


# used in show offcut
def showoffcut_target(nodename):
  vesselhandle = find_handle_for_node(nodename)
  try:
    offcutdata = nmclient_rawsay(vesselhandle,"GetOffcutResources")
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, offcutdata)
  




def browse_target(node, currentkeyname):

  # NOTE: I almost think I should skip those nodes that I know about from 
  # previous browse commands.   Perhaps I should have an option on the browse
  # command?

  host, portstring = node.split(':')
  port = int(portstring)

  # get information about the node's vessels
  try:
    nodehandle = nmclient_createhandle(host, port, privatekey = keys[currentkeyname]['privatekey'], publickey = keys[currentkeyname]['publickey'])
  except NMClientException,e:
    return (False, str(e))

  try:
    # need to contact the node to get the list of vessels we can perform
    # actions on...
    ownervessels, uservessels = nmclient_listaccessiblevessels(nodehandle,keys[currentkeyname]['publickey'])

    retlist = []

    # we should add anything we can access (whether a user or owner vessel)
    for vesselname in ownervessels + uservessels:
      longname = host+":"+str(port)+":"+vesselname

      # if we haven't discovered the vessel previously...
      if longname not in targets:
        # set the vesselname in the handle
        newhandle = nmclient_duplicatehandle(nodehandle)
        handleinfo = nmclient_get_handle_info(newhandle)
        handleinfo['vesselname'] = vesselname
        nmclient_set_handle_info(newhandle, handleinfo)

        # then add the vessel to the target list, etc.
        # add_vessel has no race conditions as long as longname is unique 
        # (and it should be unique)
        id = add_vessel(longname,currentkeyname,newhandle)
        targets['browsegood'].append(longname)

        # and append some information to be printed...
        retlist.append('%'+str(id)+"("+longname+")")



  finally:
    nmclient_destroyhandle(nodehandle)

  return (True, retlist)


def list_or_update_target(longname):

  vesselname = vesselinfo[longname]['vesselname']
  try:
    vesseldict = nmclient_getvesseldict(vesselinfo[longname]['handle'])
  except NMClientException, e:
    return (False, str(e))
  else:
    # updates the dictionary of our node information (dictionary used in show, 
    # etc.)
    for key in vesseldict['vessels'][vesselname]:
      vesselinfo[longname][key] = vesseldict['vessels'][vesselname][key]
    return (True,)


def upload_target(longname, remotefn, filedata):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # add the file data...
    nmclient_signedsay(vesselinfo[longname]['handle'], "AddFileToVessel", vesselname, remotefn, filedata)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)


def download_target(longname,localfn,remotefn):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # get the file data...
    retrieveddata = nmclient_signedsay(vesselinfo[longname]['handle'], "RetrieveFileFromVessel", vesselname, remotefn)

  except NMClientException, e:
    return (False, str(e))

  else:
    writefn = localfn+"."+longname.replace(':','_')
    # write to the local filename (replacing ':' with '_')...
    fileobj = open(writefn,"w")
    fileobj.write(retrieveddata)
    fileobj.close()
    # for output...
    return (True, writefn)



def delete_target(longname,remotefn):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # delete the file...
    nmclient_signedsay(vesselinfo[longname]['handle'], "DeleteFileInVessel", vesselname, remotefn)

  except NMClientException, e:
    return (False, str(e))

  else:
    return (True,)


def start_target(longname, argstring):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # start the program
    nmclient_signedsay(vesselinfo[longname]['handle'], "StartVessel", vesselname, argstring)

  except NMClientException, e:
    return (False, str(e))

  else:
    return (True,)


def stop_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # stop the programs
    nmclient_signedsay(vesselinfo[longname]['handle'], "StopVessel", vesselname)
  except NMClientException, e:
    return (False, str(e))

  else:
    return (True,)



def run_target(longname,filename,filedata, argstring):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    nmclient_signedsay(vesselinfo[longname]['handle'], "AddFileToVessel", vesselname, filename, filedata)
    nmclient_signedsay(vesselinfo[longname]['handle'], "StartVessel", vesselname, argstring)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)



# didn't test...
def split_target(longname, resourcedata):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    newvesselnames = nmclient_signedsay(vesselinfo[longname]['handle'], "SplitVessel", vesselname, resourcedata)
  except NMClientException, e:
    return (False, str(e))
  else:
    newname1 = copy_vessel(longname, newvesselnames.split()[0])
    newname2 = copy_vessel(longname, newvesselnames.split()[1])
    delete_vessel(longname)
    return (True,(newname1,newname2))


# didn't test...
def join_target(nodename,nodedict):
 
  if len(nodedict[nodename]) < 2:
    # not enough vessels, nothing to do
    return (False, None)
            

  # I'll iterate through the vessels, joining one with the current 
  # (current starts as the first vessel and becomes the "new vessel")
  currentvesselname = vesselinfo[nodedict[nodename][0]]['vesselname']
  currentlongname = nodedict[nodename][0]

  # keep a list of what I replace...
  subsumedlist = [currentlongname]

  for longname in nodedict[nodename][1:]:
    vesselname = vesselinfo[longname]['vesselname']
    try:
      newvesselname = nmclient_signedsay(vesselinfo[longname]['handle'], "JoinVessels", currentvesselname, vesselname)
    except NMClientException, e:
      return (False, str(e))
    else:
      newname = copy_vessel(longname, newvesselname)
      delete_vessel(longname)
      delete_vessel(currentlongname)
      subsumedlist.append(longname)
      currentlongname = newname
      currentvesselname = newvesselname
  else:
    return (True, (currentlongname,subsumedlist))



# didn't test...
def setowner_target(longname,newowner):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeOwner", vesselname, rsa_publickey_to_string(keys[newowner]['publickey']))
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)
  


# didn't test...
def setadvertise_target(longname,newadvert):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # do the actual advertisement changes
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeAdvertise", vesselname, newadvert)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)
  

def setownerinformation_target(longname,newownerinformation):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # do the actual advertisement changes
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeOwnerInformation", vesselname, newownerinformation)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)
  

def setusers_target(longname,userkeystring):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeUsers", vesselname, userkeystring)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)




#################### main loop and variables.
  
# a dict that contains all of the targets (vessels and groups) we know about.
targets = {'%all':[]}

# stores information about the vessels...
vesselinfo = {}

# the nextid that should be used for a new target.
nextid = 1

# a dict that contains all of the key information
keys = {}



# The usual way of handling a user request is:
#   1) parse the arguments the user gives (I do this up front so that I can
#      give intelligible error messages before doing any work)
#   2) handle the request.   If the request can be handled with local data, 
#      it does so.   Otherwise, contact_targets is called with the list of
#      of targets.   (targets are usually either nodenames or longnames)
#   3) provide output to the user informing them of what happened.   It is
#      common to create groups for the user if different targets have different
#      outcomes
#
# Steps 1 and 3 are always done inline (inflating the function length).   Step
# 2 is commonly done by a function XXX_target(...) listed above

def command_loop():
  # things that may be set herein and used in later commands
  host = None
  port = None
  expnum = None
  filename = None
  cmdargs = None
  defaulttarget = None
  defaultkeyname = None


  # exit via a return
  while True:

    try:
      
      
      prompt = ''
      if defaultkeyname:
        prompt = fit_string(defaultkeyname,20)+"@"

      # display the thing they are acting on in their prompt (if applicable)
      if defaulttarget:
        prompt = prompt + fit_string(defaulttarget,20)

      prompt = prompt + " !> "
      # the prompt should look like: justin@good !> 

      # get the user input
      userinput = raw_input(prompt)

      userinput = userinput.strip()

      userinputlist = userinput.split()
      if len(userinputlist)==0:
        continue

      # by default, use the target specified in the prompt
      currenttarget = defaulttarget

      # set the target, then handle other operations
      if len(userinputlist) >= 2:
        if userinputlist[0] == 'on':
          if userinputlist[1] not in targets:
            raise UserError("Error: Unknown target '"+userinputlist[1]+"'")
          # set the target and strip the rest...
          currenttarget = userinputlist[1]
          userinputlist = userinputlist[2:]

          # they are setting the default
          if len(userinputlist) == 0:
            defaulttarget = currenttarget
            continue

      # by default, use the identity specified in the prompt
      currentkeyname = defaultkeyname

      # set the keys, then handle other operations
      if len(userinputlist) >= 2:
        if userinputlist[0] == 'as':
          if userinputlist[1] not in keys:
            raise UserError("Error: Unknown identity '"+userinputlist[1]+"'")
          # set the target and strip the rest...
          currentkeyname = userinputlist[1]
          userinputlist = userinputlist[2:]

          # they are setting the default
          if len(userinputlist) == 0:
            defaultkeyname = currentkeyname
            continue





# help or ?
      if userinputlist[0] == 'help' or userinputlist[0] == '?':
        if len(userinputlist) == 1:
          print \
"""
A target can be either a host:port:vesselname, %ID, or a group name.

on target [command] -- Runs a command on a target (or changes the default)
as keyname [command]-- Run a command using an identity (or changes the default).
add [target] [to group]      -- Adds a target to a new or existing group 
remove [target] [from group] -- Removes a target from a group
show                -- Displays shell state (use 'help show' for more info)
set                 -- Changes the state of the targets (use 'help set')
browse              -- Find vessels I can control
genkeys fn [len] [as identity] -- creates new pub / priv keys (default len=1024)
loadkeys fn [as identity]   -- loads filename.publickey and filename.privatekey
list               -- Update and display information about the vessels
upload localfn (remotefn)   -- Upload a file 
download remotefn (localfn) -- Download a file 
delete remotefn             -- Delete a file
run file [args ...]    -- Shortcut for upload a file and start
start file [args ...] -- Start an experiment
stop               -- Stop an experiment
split resourcefn            -- Split another vessel off of each vessel
join                        -- Join vessels on the same node
help [help | set | show ]    -- help information 
exit                         -- exits the shell
"""
#!resourcedata                -- List resource information about the vessel

        else:
          if userinputlist[1] == 'set':
            print \
"""set users [ identity ... ]  -- Change a vessel's users
set ownerinfo [ data ... ]    -- Change owner information for the vessels
set advertise [ on | off ] -- Change advertisement of vessels
set owner identity        -- Change a vessel's owner
"""


          elif userinputlist[1] == 'show':
            print \
"""
show users      -- Display the user keys for the vessels
show ownerinfo  -- Display owner information for the vessels
show advertise  -- Display advertisement information about the vessels
show owner      -- Display a vessel's owner
show targets    -- Display a list of targets
show identities -- Display the known identities
show keys       -- Display the known keys
show log        -- Display the log from the node (*)
show resources  -- Display the resources / restrictions for the vessel (*)
show offcut     -- Display the offcut resource for the node (*)
show ip         -- Display the ip addresses of the nodes

(*) No need to update prior, the command contacts the nodes anew
"""


          elif userinputlist[1] == 'help':
            print \
"""
Extended commands (not commonly used):

loadpub fn [as identity]    -- loads filename.publickey 
loadpriv fn [as identity]   -- loads filename.privatekey
move target to group        -- Add target to group, remove target from default
contact host:port[:vessel] -- Communicate with a node
update             -- Update information about the vessels
"""
          else:
            raise UserError("Usage: help [ set | show ] -- display help")


        continue





# exit, quit, bye
      elif userinputlist[0] == 'exit' or userinputlist[0] == 'quit' or userinputlist[0] == 'bye':
        return







# show   (lots to do here)
      elif userinputlist[0] == 'show':
        if len(userinputlist) == 1:
          # What do I show?
          pass

# show targets    -- Display a list of targets
        elif userinputlist[1] == 'targets' or userinputlist[1] == 'groups':
          for target in targets:
            if len(targets[target]) == 0:
              print target, "(empty)"
              continue
            # this is a vesselentry
            if target == targets[target][0]:
              continue
            print target, targets[target]


        elif userinputlist[1] == 'keys':
          for identity in keys:
            print identity,keys[identity]['publickey'],keys[identity]['privatekey']




# show identities -- Display the known identities
        # catch a common typo
        elif userinputlist[1] == 'identities' or userinputlist[1] == 'identites':
          for keyname in keys:
            print keyname,
            if keys[keyname]['publickey']:
              print "PUB",
            if keys[keyname]['privatekey']:
              print "PRIV",
            print



# show users      -- Display the user keys for the vessels
        elif userinputlist[1] == 'users':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'userkeys' in vesselinfo[longname]:
              if vesselinfo[longname]['userkeys'] == []:
                print longname,"(no keys)"
                continue

              print longname,
              # we'd like to say 'joe's public key' instead of '3453 2323...'
              for key in vesselinfo[longname]['userkeys']:
                for identity in keys:
                  if keys[identity]['publickey'] == key:
                    print identity,
                    break
                else:
                  print fit_string(rsa_publickey_to_string(key),15),
              print
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue

# show ownerinfo  -- Display owner information for the vessels
        elif userinputlist[1] == 'ownerinfo':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'ownerinfo' in vesselinfo[longname]:
              print longname, "'"+vesselinfo[longname]['ownerinfo']+"'"
              # list all of the info...
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue

# show advertise  -- Display advertisement information about the vessels
        elif userinputlist[1] == 'advertise':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'advertise' in vesselinfo[longname]:
              if vesselinfo[longname]['advertise']:
                print longname, "on"
              else:
                print longname, "off"
              # list all of the info...
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue


# show owner      -- Display a vessel's owner
        elif userinputlist[1] == 'owner':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'ownerkey' in vesselinfo[longname]:
              # we'd like to say 'joe public key' instead of '3453 2323...'
              ownerkey = vesselinfo[longname]['ownerkey']
              for identity in keys:
                if keys[identity]['publickey'] == ownerkey:
                  print longname, identity+" pubkey"
                  break
              else:
                print longname, fit_string(rsa_publickey_to_string(ownerkey),15)
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue


# show log        -- Display the log from the node (*)
        elif userinputlist[1] == 'log' or userinputlist[1] == 'logs':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          # print the vessel logs...
          retdict = contact_targets(targets[currenttarget], showlog_target)

          goodlist = []
          faillist = []
          for longname in retdict:
            # True means it worked
            if retdict[longname][0]:
              print "Log from '"+longname+"':"
              print retdict[longname][1]
              goodlist.append(longname)
            else:
              print "failure:",retdict[longname][1]
              faillist.append(longname)
  
          # and display it...
          if faillist:
            print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
          if goodlist and faillist:
            targets['loggood'] = goodlist
            targets['logfail'] = faillist
            print "Added group 'loggood' with "+str(len(targets['loggood']))+" targets and 'logfail' with "+str(len(targets['logfail']))+" targets"

          continue




# show resources  -- Display the resources / restrictions for the vessel (*)
        elif userinputlist[1] == 'resource' or userinputlist[1] == 'resources':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          retdict = contact_targets(targets[currenttarget], showresources_target)
          faillist = []
          goodlist = []
          for longname in retdict:
            # True means it worked
            if retdict[longname][0]:
              print "Resource data for '"+longname+"':"
              print retdict[longname][1]
              goodlist.append(longname)
            else:
              print "failure:",retdict[longname][1]
              faillist.append(longname)
  
          # and display it...
          if faillist:
            print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
          if goodlist and faillist:
            targets['resourcegood'] = goodlist
            targets['resourcefail'] = faillist
            print "Added group 'resourcegood' with "+str(len(targets['resourcegood']))+" targets and 'resourcefail' with "+str(len(targets['resourcefail']))+" targets"

          continue



# show offcut     -- Display the offcut resource for the node (*)
        elif userinputlist[1] == 'offcut':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          
          # we should only visit a node once...
          nodelist = listops_uniq(longnamelist_to_nodelist(targets[currenttarget]))
          retdict = contact_targets(nodelist, showoffcut_target)

          for nodename in retdict:
            if retdict[nodename][0]:
              print "Offcut resource data for '"+nodename+"':"
              print retdict[nodename][1]
            else:
              print "failure:",retdict[nodename][1]
  
          continue



# show ip         -- Display the ip addresses of the nodes
        # catch a misspelling
        elif userinputlist[1] == 'ip' or userinputlist[1] == 'ips':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          
          # we should only visit a node once...
          printedIPlist = []
          for longname in targets[currenttarget]:
            thisnodeIP = vesselinfo[longname]['IP']

            if thisnodeIP not in printedIPlist:
              printedIPlist.append(thisnodeIP)
              print thisnodeIP
  
          continue









# show ???      -- oops!
        else:
          raise UserError("Error in usage: try 'help show'")
        continue






# add (target) (to group)
      elif userinputlist[0] == 'add':
        if len(userinputlist) == 2:
          source = userinputlist[1]
          dest = currenttarget

        elif len(userinputlist) == 3:
          source = currenttarget
          if userinputlist[1] != 'to':
            raise UserError("Error, command format: add (target) (to group)")
          dest = userinputlist[2]

        elif len(userinputlist) == 4:
          source = userinputlist[1]
          if userinputlist[2] != 'to':
            raise UserError("Error, command format: add (target) (to group)")
          dest = userinputlist[3]

        else:
          raise UserError("Error, command format: add (target) (to group)")
 
        # okay, now source and dest are set.   Time to add the nodes in source
        # to the group dest...
        if source not in targets:
          raise UserError("Error, unknown target '"+source+"'")
        if dest not in targets:
          if not valid_targetname(dest):
            raise UserError("Error, invalid target name '"+dest+"'")
          targets[dest] = []

        if is_immutable_targetname(dest):
          raise UserError("Can't modify the contents of '"+dest+"'")

        # source - dest has what we should add (items in source but not dest)
        addlist = listops_difference(targets[source],targets[dest])
        if len(addlist) == 0:
          raise UserError("No targets to add (the target is already in '"+dest+"')")
        
        for item in addlist:
          targets[dest].append(item)
        continue







# remove (target) (from group)
      elif userinputlist[0] == 'remove':
        if len(userinputlist) == 2:
          source = userinputlist[1]
          dest = currenttarget

        elif len(userinputlist) == 3:
          source = currenttarget
          if userinputlist[1] != 'from':
            raise UserError("Error, command format: remove (target) (from group)")
          dest = userinputlist[2]

        elif len(userinputlist) == 4:
          source = userinputlist[1]
          if userinputlist[2] != 'from':
            raise UserError("Error, command format: remove (target) (from group)")
          dest = userinputlist[3]

        else:
          raise UserError("Error, command format: remove (target) (from group)")
 
        # time to check args and do the ops
        if source not in targets:
          raise UserError("Error, unknown target '"+source+"'")
        if dest not in targets:
          raise UserError("Error, unknown group '"+dest+"'")

        if is_immutable_targetname(dest):
          raise UserError("Can't modify the contents of '"+dest+"'")

        # find the items to remove (the items in both dest and source)
        removelist = listops_intersect(targets[dest],targets[source])
        if len(removelist) == 0:
          raise UserError("No targets to remove (no items from '"+source+"' are in '"+dest+"')")

        # it's okay to end up with an empty group.   We'll leave it...
        for item in removelist:
          targets[dest].remove(item)

        continue
          





# move target to group
      elif userinputlist[0] == 'move':
        if len(userinputlist) == 4:
          moving = userinputlist[1]
          source = currenttarget
          if userinputlist[2] != 'to':
            raise UserError("Error, command format: move target to group")
          dest = userinputlist[3]

        else:
          raise UserError("Error, command format: move target to group")
 
        # check args...
        if source not in targets:
          raise UserError("Error, unknown group '"+source+"'")
        if moving not in targets:
          raise UserError("Error, unknown group '"+moving+"'")
        if dest not in targets:
          raise UserError("Error, unknown group '"+dest+"'")


        if is_immutable_targetname(dest):
          raise UserError("Can't modify the contents of '"+source+"'")

        if is_immutable_targetname(dest):
          raise UserError( "Can't modify the contents of '"+dest+"'")

        removelist = listops_intersect(targets[source], targets[moving])
        if len(removelist) == 0:
          raise UserError("Error, '"+moving+"' is not in '"+source+"'")

        addlist = listops_difference(removelist, targets[dest])
        if len(addlist) == 0:
          raise UserError("Error, the common items between '"+source+"' and '"+moving+"' are already in '"+dest+"'")

        for item in removelist:
          targets[source].remove(item)

        for item in addlist:
          targets[dest].append(item)

        continue







# contact host:port[:vessel] -- Communicate with a node
      elif userinputlist[0] == 'contact':
        if currentkeyname == None or not keys[currentkeyname]['publickey']:
          raise UserError("Error, must contact as an identity")

        if len(userinputlist)>2:
          raise UserError("Error, usage is contact host:port[:vessel]")

        if len(userinputlist[1].split(':')) == 2:
          host, portstring = userinputlist[1].split(':')
          port = int(portstring)
          vesselname = None
        elif len(userinputlist[1].split(':')) == 3:
          host, portstring,vesselname = userinputlist[1].split(':')
          port = int(portstring)
        else:
          raise UserError("Error, usage is contact host:port[:vessel]")
        
        # get information about the node's vessels
        thishandle = nmclient_createhandle(host, port, privatekey = keys[currentkeyname]['privatekey'], publickey = keys[currentkeyname]['publickey'], vesselid = vesselname)
        ownervessels, uservessels = nmclient_listaccessiblevessels(thishandle,keys[currentkeyname]['publickey'])

        newidlist = []
        # determine if we control the specified vessel...
        if vesselname:
          if vesselname in ownervessels or vesselname in uservessels:
            longname = host+":"+str(port)+":"+vesselname
            # no need to set the vesselname, we did so above...
            id = add_vessel(longname,currentkeyname,thishandle)
            newidlist.append('%'+str(id)+"("+longname+")")
          else:
            raise UserError("Error, cannot access vessel '"+vesselname+"'")

        # we should add anything we can access
        else:
          for vesselname in ownervessels:
            longname = host+":"+str(port)+":"+vesselname
            if longname not in targets:
              # set the vesselname
              # NOTE: we leak handles (no cleanup of thishandle).   
              # I think we don't care...
              newhandle = nmclient_duplicatehandle(thishandle)
              handleinfo = nmclient_get_handle_info(newhandle)
              handleinfo['vesselname'] = vesselname
              nmclient_set_handle_info(newhandle, handleinfo)

              id = add_vessel(longname,currentkeyname,newhandle)
              newidlist.append('%'+str(id)+"("+longname+")")

          for vesselname in uservessels:
            longname = host+":"+str(port)+":"+vesselname
            if longname not in targets:
              # set the vesselname
              # NOTE: we leak handles (no cleanup of thishandle).   
              # I think we don't care...
              newhandle = nmclient_duplicatehandle(thishandle)
              handleinfo = nmclient_get_handle_info(newhandle)
              handleinfo['vesselname'] = vesselname
              nmclient_set_handle_info(newhandle, handleinfo)

              id = add_vessel(longname,currentkeyname,newhandle)
              newidlist.append('%'+str(id)+"("+longname+")")

        # tell the user what we did...
        if len(newidlist) == 0:
          print "Could not add any targets."
        else:
          print "Added targets: "+", ".join(newidlist)
            
        continue
  





# browse                               -- Find experiments I can control
      elif userinputlist[0] == 'browse':
        if currentkeyname == None or not keys[currentkeyname]['publickey']:
          raise UserError("Error, must browse as an identity with a public key")
  
        # they are trying to only do some types of lookup...
        if len(userinputlist) > 1:
          nodelist = advertise.lookup(keys[currentkeyname]['publickey'],lookuptype=userinputlist[1:])
        else:
          nodelist = advertise.lookup(keys[currentkeyname]['publickey'])

        # If there are no vessels for a user, the lookup may return ''
        for nodename in nodelist[:]:
          if nodename == '':
            nodelist.remove(nodename)

        # we'll output a message about the new keys later...
        newidlist = []

        faillist = []

        targets['browsegood'] = []

        print nodelist
        # currently, if I browse more than once, I look up everything again...
        retdict = contact_targets(nodelist,browse_target, currentkeyname)

        # parse the output so we can print out something intelligible
        for nodename in retdict:
          
          if retdict[nodename][0]:
            newidlist = newidlist + retdict[nodename][1]
          else:
            print "Error '",retdict[nodename][1],"' on "+nodename
            faillist.append(nodename)


        # tell the user what we did...
        if len(faillist) > 0:
          print "Failed to contact: "+ ", ".join(faillist)

        if len(newidlist) == 0:
          print "Could not add any new targets."
        else:
          print "Added targets: "+", ".join(newidlist)

        if len(targets['browsegood']) > 0:
          print "Added group 'browsegood' with "+str(len(targets['browsegood']))+" targets"
              
        continue





# genkeys filename [len] [as identity]          -- creates keys
      elif userinputlist[0] == 'genkeys':
        if len(userinputlist)==2:
          keylength = 1024
          keyname = userinputlist[1]
          pubkeyfn = keyname+'.publickey'
          privkeyfn = keyname+'.privatekey'
        elif len(userinputlist)==3:
          keylength = int(userinputlist[2])
          keyname = userinputlist[1]
          pubkeyfn = keyname+'.publickey'
          privkeyfn = keyname+'.privatekey'
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: genkeys filename [len] [as identity]")
          keylength = 1024
          keyname = userinputlist[3]
          pubkeyfn = userinputlist[1]+'.publickey'
          privkeyfn = userinputlist[1]+'.privatekey'
        elif len(userinputlist)==5:
          if userinputlist[3] != 'as':
            raise UserError("Usage: genkeys filename [len] [as identity]")
          keylength = int(userinputlist[2])
          keyname = userinputlist[4]
          pubkeyfn = userinputlist[1]+'.publickey'
          privkeyfn = userinputlist[1]+'.privatekey'
        else:
          raise UserError("Usage: genkeys filename [len] [as identity]")
  

        # do the actual generation (will take a while)
        newkeys = rsa_gen_pubpriv_keys(keylength)
        
        rsa_privatekey_to_file(newkeys[1],privkeyfn)
        rsa_publickey_to_file(newkeys[0],pubkeyfn)
        keys[keyname] = {'publickey':newkeys[0], 'privatekey':newkeys[1]}

        print "Created identity '"+keyname+"'"
        continue
  




# loadpub filename [as identity]                    -- loads a public key
      elif userinputlist[0] == 'loadpub':
        if len(userinputlist)==2:
          # they typed 'loadpub foo.publickey'
          if userinputlist[1].endswith('.publickey'):
            keyname = userinputlist[1][:len('.publickey')]
            pubkeyfn = userinputlist[1]
          else:
            # they typed 'loadpub foo'
            keyname = userinputlist[1]
            pubkeyfn = userinputlist[1]+'.publickey'
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: loadpub filename [as identity]")

          # they typed 'loadpub foo.publickey'
          if userinputlist[1].endswith('.publickey'):
            pubkeyfn = userinputlist[1]
          else:
            # they typed 'loadpub foo'
            pubkeyfn = userinputlist[1]+'.publickey'
          keyname = userinputlist[3]
        else:
          raise UserError("Usage: loadpub filename [as identity]")

        # load the key and update the table...
        pubkey = rsa_file_to_publickey(pubkeyfn)
        if keyname not in keys:
          keys[keyname] = {'publickey':pubkey, 'privatekey':None}
        else:
          keys[keyname]['publickey'] = pubkey

        continue
  




# loadpriv filename [as identity]                    -- loads a private key
      elif userinputlist[0] == 'loadpriv':
        if len(userinputlist)==2:
          # they typed 'loadpriv foo.privatekey'
          if userinputlist[1].endswith('.privatekey'):
            keyname = userinputlist[1][:len('.privatekey')]
            privkeyfn = userinputlist[1]
          else:
            # they typed 'loadpriv foo'
            keyname = userinputlist[1]
            privkeyfn = keyname+'.privatekey'
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: loadpriv filename [as identity]")

          # they typed 'loadpriv foo.privatekey'
          if userinputlist[1].endswith('.privatekey'):
            privkeyfn = userinputlist[1]
          else:
            # they typed 'loadpriv foo'
            privkeyfn = userinputlist[1]+'.privatekey'
          keyname = userinputlist[3]
        else:
          raise UserError("Usage: loadpriv filename [as identity]")

        # load the key and update the table...
        privkey = rsa_file_to_privatekey(privkeyfn)
        if keyname not in keys:
          keys[keyname] = {'privatekey':privkey, 'publickey':None}
        else:
          keys[keyname]['privatekey'] = privkey

        continue




# loadkeys filename [as identity]                    -- loads a private key
      elif userinputlist[0] == 'loadkeys':
        if len(userinputlist)==2:
          # they typed 'loadpriv foo'
          keyname = userinputlist[1]
          privkeyfn = keyname+'.privatekey'
          pubkeyfn = keyname+'.publickey'
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: loadkeys filename [as identity]")

          keyname = userinputlist[3]
          privkeyfn = userinputlist[1]+'.privatekey'
          pubkeyfn = userinputlist[1]+'.publickey'
        else:
          raise UserError("Usage: loadkeys filename [as identity]")

        # load the keys and update the table...
        privkey = rsa_file_to_privatekey(privkeyfn)
        pubkey = rsa_file_to_publickey(pubkeyfn)
        keys[keyname] = {'privatekey':privkey, 'publickey':pubkey}

        continue




# list               -- Update and display information about the vessels

# output looks similar to:
#  ID Own                       Name     Status              Owner Information
#  %1  *       128.208.3.173:1224:v5      Fresh                               
#  %2  *        128.208.3.86:1224:v2      Fresh                               
#  %3          234.17.98.23:53322:v5    Stopped               Chord experiment
#
      elif userinputlist[0] == 'list':
        if len(userinputlist)>1:
          raise UserError("Usage: list")

        if not currenttarget:
          raise UserError("Must specify a target")
        
        # update information about the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],list_or_update_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Error '"+retdict[longname][1]+"' on "+longname
            faillist.append(longname)

        # and display it...
        if faillist:
          print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
        if goodlist:
          print "%4s %3s %25s %10s %30s" % ('ID','Own','Name','Status','Owner Information')

        # walk through target to print instead of the good list so that the
        # names are printed in order...
        for longname in targets[currenttarget]:
          if longname in goodlist:  
            if keys[currentkeyname]['publickey'] == vesselinfo[longname]['ownerkey']:
              owner = '*'
            else:
              owner = ''
            print "%4s  %1s  %25s %10s %30s" % (vesselinfo[longname]['ID'],owner,fit_string(longname,25),vesselinfo[longname]['status'],fit_string(vesselinfo[longname]['ownerinfo'],30))

        # add groups for fail and good (if there is a difference in what nodes do)
        if goodlist and faillist:
          targets['listgood'] = goodlist
          targets['listfail'] = faillist
          print "Added group 'listgood' with "+str(len(targets['listgood']))+" targets and 'listfail' with "+str(len(targets['listfail']))+" targets"


        statusdict = {}
        # add status groups (if there is a difference in vessel state)
        for longname in goodlist:
          if vesselinfo[longname]['status'] not in statusdict:
            # create a list with this element...
            statusdict[vesselinfo[longname]['status']] = []
          statusdict[vesselinfo[longname]['status']].append(longname)

        if len(statusdict) > 1:
          print "Added group",
          for statusname in statusdict:
            targets['list'+statusname] = statusdict[statusname]
            print "'"+statusname+"' with "+str(len(targets['list'+statusname]))+" targets",
          print
          
        continue
  

# update
      elif userinputlist[0] == 'update':
        if len(userinputlist)>1:
          raise UserError("Usage: update")

        if not currenttarget:
          raise UserError("Must specify a target")
        
        # update information about the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],list_or_update_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Error '"+retdict[longname][1]+"' on "+longname
            faillist.append(longname)

        # and display it...
        if faillist:
          print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
        if goodlist and faillist:
          targets['updategood'] = goodlist
          targets['updatefail'] = faillist
          print "Added group 'updategood' with "+str(len(targets['updategood']))+" targets and 'updatefail' with "+str(len(targets['updatefail']))+" targets"

        continue
  




# upload localfn (remotefn)   -- Upload a file 
      elif userinputlist[0] == 'upload':
        if len(userinputlist)==2:
          remotefn = userinputlist[1]
          localfn = userinputlist[1]
        elif len(userinputlist)==3:
          localfn = userinputlist[1]
          remotefn = userinputlist[2]
        else:
          raise UserError("Usage: upload localfn (remotefn)")

        if not currenttarget:
          raise UserError("Must specify a target")
  

        # read the local file...
        fileobj = open(localfn,"r")
        filedata = fileobj.read()
        fileobj.close()

        # add the file to the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],upload_target, remotefn, filedata)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' uploading to",longname
            faillist.append(longname)

        # update the groups
        if goodlist and faillist:
          targets['uploadgood'] = goodlist
          targets['uploadfail'] = faillist
          print "Added group 'uploadgood' with "+str(len(targets['uploadgood']))+" targets and 'uploadfail' with "+str(len(targets['uploadfail']))+" targets"

  
        continue
  


# download remotefn (localfn) -- Download a file 
      elif userinputlist[0] == 'download':
        if len(userinputlist)==2:
          remotefn = userinputlist[1]
          localfn = userinputlist[1]
        elif len(userinputlist)==3:
          localfn = userinputlist[1]
          remotefn = userinputlist[2]
        else:
          raise UserError("Usage: download localfn (remotefn)")

        if not currenttarget:
          raise UserError("Must specify a target")
  


        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],download_target,localfn,remotefn)

        writestring = ''
        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
            # for output...
            writestring = writestring + retdict[longname][1]+ " "
          else:
            print "Failure '"+retdict[longname][1]+"' downloading from",longname
            faillist.append(longname)

        if writestring:
          print "Wrote files: "+writestring

        # add groups if needed...
        if goodlist and faillist:
          targets['downloadgood'] = goodlist
          targets['downloadfail'] = faillist
          print "Added group 'downloadgood' with "+str(len(targets['downloadgood']))+" targets and 'downloadfail' with "+str(len(targets['downloadfail']))+" targets"

  
        continue
  



# delete remotefn             -- Delete a file
      elif userinputlist[0] == 'delete':
        if len(userinputlist)==2:
          remotefn = userinputlist[1]
        else:
          raise UserError("Usage: delete remotefn")

        if not currenttarget:
          raise UserError("Must specify a target")
  

        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],delete_target, remotefn)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else: 
            print "Failure '"+retdict[longname][1]+"' deleting on",longname
            faillist.append(longname)

        # add groups if needed...
        if goodlist and faillist:
          targets['deletegood'] = goodlist
          targets['deletefail'] = faillist
          print "Added group 'deletegood' with "+str(len(targets['deletegood']))+" targets and 'deletefail' with "+str(len(targets['deletefail']))+" targets"

  
        continue
  

  
# start file [args ...]  -- Start an experiment
      elif userinputlist[0] == 'start':
        if len(userinputlist)>1:
          argstring = ' '.join(userinputlist[1:])
        else:
          raise UserError("Usage: start file [args ...]")

        if not currenttarget:
          raise UserError("Must specify a target")
  
        # need to get the status, etc (or do I just try to start them all?)
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],start_target, argstring)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' starting ",longname
            faillist.append(longname)

        # add groups if needed...
        if goodlist and faillist:
          targets['startgood'] = goodlist
          targets['startfail'] = faillist
          print "Added group 'startgood' with "+str(len(targets['startgood']))+" targets and 'startfail' with "+str(len(targets['startfail']))+" targets"

  

# stop               -- Stop an experiment
      elif userinputlist[0] == 'stop':
        if len(userinputlist)>1:
          raise UserError("Usage: stop")

        if not currenttarget:
          raise UserError("Must specify a target")
  
        # need to get the status, etc (or do I just try to stop them all?)
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],stop_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' stopping ",longname
            faillist.append(longname)



        # add groups if needed...
        if goodlist and faillist:
          targets['stopgood'] = goodlist
          targets['stopfail'] = faillist
          print "Added group 'stopgood' with "+str(len(targets['stopgood']))+" targets and 'stopfail' with "+str(len(targets['stopfail']))+" targets"



# run file [args...]    -- Shortcut for upload a file and start
      elif userinputlist[0] == 'run':
        if len(userinputlist)>1:
          filename = userinputlist[1]
          argstring = " ".join(userinputlist[1:])
        else:
          raise UserError("Usage: run file [args ...]")

        if not currenttarget:
          raise UserError("Must specify a target")
  

        # read the local file...
        fileobj = open(filename,"r")
        filedata = fileobj.read()
        fileobj.close()

        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],run_target,filename,filedata, argstring)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' on ",longname
            faillist.append(longname)


        # update the groups
        if goodlist and faillist:
          targets['rungood'] = goodlist
          targets['runfail'] = faillist
          print "Added group 'rungood' with "+str(len(targets['rungood']))+" targets and 'runfail' with "+str(len(targets['runfail']))+" targets"

  
        continue
  





#split resourcefn            -- Split off of each vessel another vessel

      elif userinputlist[0] == 'split':
        if len(userinputlist)==2:
          resourcefn = userinputlist[1]
        else:
          raise UserError("Usage: split resourcefn")

        if not currenttarget:
          raise UserError("Must specify a target")

        resourcefo = open(resourcefn)
        resourcedata = resourcefo.read()
        resourcefo.close() 
  

        faillist = []
        goodlist1 = []
        goodlist2 = []

        retdict = contact_targets(targets[currenttarget],split_target,resourcedata)

        for longname in retdict:
          if retdict[longname][0]:
            newname1, newname2 = retdict[longname][1]
            goodlist1.append(newname1)
            goodlist2.append(newname2)
            print longname+" -> ("+newname1+", "+newname2+")"
          else:
            print "Failure '"+retdict[longname][1]+"' splitting",longname
            faillist.append(longname)

        # update the groups
        if goodlist1 and goodlist2 and faillist:
          targets['split1'] = goodlist1
          targets['split2'] = goodlist2
          targets['splitfail'] = faillist
          print "Added group 'split1' with "+str(len(targets['split1']))+" targets, 'split2' with "+str(len(targets['split2']))+" targets and 'splitfail' with "+str(len(targets['splitfail']))+" targets"
        elif goodlist1 and goodlist2:
          targets['split1'] = goodlist1
          targets['split2'] = goodlist2
          print "Added group 'split1' with "+str(len(targets['split1']))+" targets and 'split2' with "+str(len(targets['split2']))+" targets"

  
        continue




#join                        -- Join vessels on the same node

      elif userinputlist[0] == 'join':
        if len(userinputlist)!=1:
          raise UserError("Usage: join")

        if not currenttarget:
          raise UserError("Must specify a target")

        if not currentkeyname or not keys[currentkeyname]['publickey'] or not keys[currentkeyname]['privatekey']:
          raise UserError("Must specify an identity with public and private keys...")

        nodedict = {}
        skipstring = ''
        # Need to group vessels by node...
        for longname in targets[currenttarget]:
          if keys[currentkeyname]['publickey'] != vesselinfo[longname]['ownerkey']:
            skipstring = skipstring + longname+" "
            continue

          nodename = vesselinfo[longname]['IP']+":"+str(vesselinfo[longname]['port'])
          if nodename not in nodedict:
            nodedict[nodename] = []

          nodedict[nodename].append(longname)

        # if we skip nodes, explain why
        if skipstring:
          print "Skipping "+skipstring+" because the current identity is not the owner."
          print "If you are trying to join vessels with different owners, you need"
          print "to change ownership to the same owner first"


        faillist = []
        goodlist = []

        retdict = contact_targets(nodedict.keys(),join_target,nodedict)

        for nodename in retdict:
 
          if retdict[nodename][0]:
            print retdict[nodename][1][0],"<- ("+", ".join(nodedict[nodename])+")"
            goodlist = goodlist + nodedict[nodename]
          else:
            if retdict[nodename][1]:
              print "Failure '"+retdict[nodename][1]+"' on",nodename
              faillist = faillist + nodedict[nodename]
            # Nodes that I only have one vessel on don't get added to a list...

        # update the groups
        if goodlist and faillist:
          targets['joingood'] = goodlist
          targets['joinfail'] = faillist
          print "Added group 'joingood' with "+str(len(targets['joingood']))+" targets and 'joinfail' with "+str(len(targets['joinfail']))+" targets"
        elif goodlist:
          targets['joingood'] = goodlist
          targets['joinfail'] = faillist
          print "Added group 'joingood' with "+str(len(targets['joingood']))+" targets"

  
        continue














# set                 -- Changes the state of the targets (use 'help set')
      elif userinputlist[0] == 'set':
      
  
        if len(userinputlist) == 1:
          # what do I do here?
          pass

        
# set owner identity        -- Change a vessel's owner
        elif userinputlist[1] == 'owner':
          if len(userinputlist)==3:
            newowner = userinputlist[2]
          else:
            raise UserError("Usage: set owner identity")
  
          if not currenttarget:
            raise UserError("Must specify a target")
  
          if newowner not in keys:
            raise UserError("Unknown identity: '"+newowner+"'")

          if not keys[newowner]['publickey']:
            raise UserError("No public key for '"+newowner+"'")

          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setowner_target,newadvert)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)


  
          # update the groups
          if goodlist and faillist:
            targets['ownergood'] = goodlist
            targets['ownerfail'] = faillist
            print "Added group 'ownergood' with "+str(len(targets['ownergood']))+" targets and 'ownerfail' with "+str(len(targets['ownerfail']))+" targets"
  
    
          continue
  


# set advertise [ on | off ] -- Change advertisement of vessels
        elif userinputlist[1] == 'advertise':
          if len(userinputlist)==3:
            if userinputlist[2] == 'on':
              newadvert = True
            elif userinputlist[2] == 'off':
              newadvert = False
            else:
              raise UserError("Usage: set advertise [ on | off ]")
          else:
            raise UserError("Usage: set advertise [ on | off ]")
  
          if not currenttarget:
            raise UserError("Must specify a target")
  

          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setadvertise_target,newadvert)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)


          # update the groups
          if goodlist and faillist:
            targets['advertisegood'] = goodlist
            targets['advertisefail'] = faillist
            print "Added group 'advertisegood' with "+str(len(targets['advertisegood']))+" targets and 'advertisefail' with "+str(len(targets['advertisefail']))+" targets"
  
    
          continue
  

# set ownerinfo [ data ... ]    -- Change owner information for the vessels
        elif userinputlist[1] == 'ownerinfo':
          newdata = " ".join(userinputlist[2:])
  
          if not currenttarget:
            raise UserError("Must specify a target")
  
          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setownerinformation_target,newdata)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)


          # update the groups
          if goodlist and faillist:
            targets['ownerinfogood'] = goodlist
            targets['ownerinfofail'] = faillist
            print "Added group 'ownerinfogood' with "+str(len(targets['ownerinfogood']))+" targets and 'ownerinfofail' with "+str(len(targets['ownerinfofail']))+" targets"
  
    
          continue
  

# set users [ identity ... ]  -- Change a vessel's users
        elif userinputlist[1] == 'users':
          userkeys = []

          for identity in userinputlist[2:]:
            if identity not in keys:
              raise UserError("Unknown identity: '"+identity+"'")

            if not keys[identity]['publickey']:
              raise UserError("No public key for '"+identity+"'")
          
            userkeys.append(rsa_publickey_to_string(keys[identity]['publickey']))
          # this is the format the NM expects...
          userkeystring = '|'.join(userkeys)
  
          if not currenttarget:
            raise UserError("Must specify a target")
  

          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setusers_target,userkeystring)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)
  
          # update the groups
          if goodlist and faillist:
            targets['usersgood'] = goodlist
            targets['usersfail'] = faillist
            print "Added group 'usersgood' with "+str(len(targets['usersgood']))+" targets and 'usersfail' with "+str(len(targets['usersfail']))+" targets"
  
    
          continue







# set ???  -- Bad command for set...
        else:

          print "Error: set command not understood, try 'help set'"

  

  
  


  
  

  
  
# else unknown
      else:
        print "Error: command not understood"
  

# handle errors
    except KeyboardInterrupt:
      # print or else their prompt will be indented
      print
      return
    except EOFError:
      # print or else their prompt will be indented
      print
      return
    except UserError, e:
      print e
    except:
      traceback.print_exc()
      
  
  
if __name__=='__main__':
  time_updatetime(34612)
  command_loop()
