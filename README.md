gorgon
======

gorgon. A  tool for complex HTTP loadtest in Python.


Gorgon aims to allow easy creation of relatively high loads of complex loadtests. Typically, loadtest tools like 
Tsung or ab doesn't allow a lot of control over the returning values or flow control (send this request to create an object,
use the object id to do another request)

In this regard, Gorgon aspires to be an intermediate tool between creating system tests and pure loadtesting.

This is extremelly early days, but some of the objectives:

  - Good enough performance (at least 2K req/sec). 
    -A "stub" function to test the limits of the test itself could be useful
  - Easy to use and integrate. A full (simple) test should be possible in less than 20 lines
  - Allow a test mode to check that all the calls are working as expected and debug.
  - Use multithread/multiprocess
    - Debug mode should not do this to allow easy debug.
  - Create an example/tool to read HTTP calls from a file as input
  - Good documentation
    - Give a couple of good examples on how to use it
    - Someone with a good knowledge of an API should be able to create a working script in 30 minutes
  - Good reporting
    - Interactive reporting (progress bar and stats).
    - Allow partial reporting (in case a test is too long)
    - Intially, just text report. Maybe later add graphs (Tsung graphs are nice)
  - The main development language is Python3 (hey, we are in 2014 after all), but, if easy enough, should be Python2 compatible
