import unittest
from app import app, get_db

class TestGlobalShinePlatform(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_homepage_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check brand name & umbrella divisions
        self.assertIn("GLOBAL", html)
        self.assertIn("SHINE", html)
        self.assertIn("Your Vision..! Our Premium Digital Transformation..!!", html)
        self.assertIn("Nishant Chaturvedi", html)
        self.assertIn("Abhishek Chaturvedi", html)
        self.assertIn("+91 9005874417", html)

        # Check all 10 Indian Clients in Client Appreciation / Testimonials
        clients = [
            "Dr. Abhay Mishra",
            "Dr. Ajay Shrivastava",
            "Dr. Sarvendra Vikram Singh",
            "Mr. Kunal Shrivastava",
            "Khushi Verma",
            "Mr. Manish Pathak",
            "Mr. Durgesh Dubey",
            "Sharda Devi Memorial College",
            "Mr. Sanjeev Singh",
            "Shri Siddhi Vinayak Enterprises"
        ]
        for client_name in clients:
            self.assertIn(client_name, html, f"Client {client_name} missing from testimonials section!")

    def test_seo_routes(self):
        res_sitemap = self.client.get('/sitemap.xml')
        self.assertEqual(res_sitemap.status_code, 200)
        self.assertIn('<loc>', res_sitemap.data.decode('utf-8'))

        res_robots = self.client.get('/robots.txt')
        self.assertEqual(res_robots.status_code, 200)
        self.assertIn('User-agent:', res_robots.data.decode('utf-8'))

    def test_auth_and_dashboards(self):
        # Test Login Page
        res_login_page = self.client.get('/login')
        self.assertEqual(res_login_page.status_code, 200)

        # Test Admin Login
        res_admin_login = self.client.post('/login', data=dict(username='admin', password='admin123'), follow_redirects=True)
        self.assertEqual(res_admin_login.status_code, 200)
        self.assertIn('Global Shine Master Control Console', res_admin_login.data.decode('utf-8'))

        # Test ID Card Generator for Admin
        res_id_card = self.client.get('/id-card/1')
        self.assertEqual(res_id_card.status_code, 200)
        self.assertIn('Nishant Chaturvedi', res_id_card.data.decode('utf-8'))

        # Logout
        self.client.get('/logout')

        # Test Team Login
        res_team_login = self.client.post('/login', data=dict(username='team1', password='team123'), follow_redirects=True)
        self.assertEqual(res_team_login.status_code, 200)
        self.assertIn('Team Member Workbench', res_team_login.data.decode('utf-8'))

        # Logout
        self.client.get('/logout')

        # Test Partner Login
        res_partner_login = self.client.post('/login', data=dict(username='partner1', password='partner123'), follow_redirects=True)
        self.assertEqual(res_partner_login.status_code, 200)
        self.assertIn('Partner Executive Portal', res_partner_login.data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
