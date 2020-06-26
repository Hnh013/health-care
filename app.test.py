import unittest

from app import app

# cehcking routes where user is logged in first :)

class BasicTestCase(unittest.TestCase):
		
	def test_transactions(self):
		tester = app.test_client(self)
		response = tester.post('/emp_login',data=dict(username="AdmiNM", password="AdmiN"),follow_redirects=True)
		
		response = tester.get('/transactions', content_type='html/text')
		self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
	unittest.main()
