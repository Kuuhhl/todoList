import unittest

def run_tests():
    test_directory = 'tests'  
    loader = unittest.TestLoader()
    suite = loader.discover(test_directory)

    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    if result.wasSuccessful():
        print("All tests passed!")
    else:
        print("Some tests failed.")

if __name__ == '__main__':
    run_tests()
