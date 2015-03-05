"""
Tests for pacman103 using the python unittest_ module.

Usage::
    
    ./run_all_tests.sh

Which can be found in the test module's directory.

This will run all tests defined in files matching :file:`test_*.py` in this
directory (and its children).

You can also run the tests contained in a single file using::
    
    python test_file.py

.. _unittest: http://docs.python.org/2/library/unittest.html


5 Minute Test Writers' Tutorial
-------------------------------

All test scripts should be placed in the pacman103.test module directory. Test
scripts should have a filename of the form `test_*.py` to allow them to be
discovered by `run_all_tests.sh`.

Though it doesn't matter how you organise your tests (all of them are executed
anyway), the following convention is strongly suggested:

* All tests for a particular module, e.g. pacman103/core/dao.py, should be
  contained within their own file in the test directory, e.g.
  pacman103/test/core/test_dao.py. This way it is easy to work out where the
  tests are for a particular piece of code. (Remember: test scripts must start
  with `test_`.)
* Test scripts consist of a series of testcases each of which test a medium
  sized component, for example a particular class.
* Testcases contains individual test methods which should check a specific
  behaviour of the element under test (for example, a particular method of a
  class).

Here is an example of what a test file should/could look like. It contains 1
test case which in turn contains two tests::
    
    #!/usr/bin/env python
    
    \"""
    An example test file.
    \"""
    
    import unittest
    
    # Import the module being tested
    from pacman103.some_module import *
    
    class MyTestCase(unittest.TestCase):
        \"""
        This is a test case which tests a class `Foo` in pacman103.some_module.
        
        You can define multiple test cases by creating classes inheriting
        `unittest.TestCase` in a file.
        \"""
        
        def setUp(self):
            \"""
            (Optional) Define this method to perform a set of tasts before each
            test is executed. For example, it could initialise an instance of
            the class you want to test (e.g. here Foo is from
            pacman103.some_module).
            \"""
            self.foo = Foo("Initialisation Data")
            self.foo.start()
        
        
        def tearDown(self):
            \"""
            (Optional) Define this method to perform some cleanup after each
            test has executed.
            \"""
            self.foo.stop()
        
        
        def test_add_one(self):
            \"""
            This is a test.
            
            Tests are defined as methods whose name starts with test_*. Define
            as many as you like in each test case.
            
            Various self.assert*() methods are provided which should be used to
            test for expected outcomes.
            \"""
            # Some simple tests
            self.assertEqual(self.foo.add_one(-1), 0)
            self.assertEqual(self.foo.add_one(0), 1)
            self.assertEqual(self.foo.add_one(1), 2)
            
            # This is python of course...
            for i in xrange(100):
                self.assertEqual(self.foo.add_one(i), i+1)
        
        
        def test_divide(self):
            \"""
            Another test.
            \"""
            # Value is True
            self.assertEqual(self.foo.divide(10, 2), 5)
            
            # Test that a certain exception occurs
            self.assertRaises(ZeroDivisionError, self.foo.divide(10, 0))
    
    
    # This makes the test file also runnable standalone.
    if __name__=="__main__":
        unittest.main()

For a list of assertions in unittest see `basic assertions
<http://docs.python.org/2/library/unittest.html#assert-methods>`_
"""
