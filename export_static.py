import os
import shutil
from app import app

def export_static_site():
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)

    # Copy static assets (css, images, js)
    static_src = os.path.join(os.path.dirname(__file__), 'static')
    static_dest = os.path.join(dist_dir, 'static')
    if os.path.exists(static_src):
        shutil.copytree(static_src, static_dest)

    # Render pages with test client
    with app.test_client() as client:
        # Home page
        res = client.get('/')
        with open(os.path.join(dist_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(res.data.decode('utf-8'))

        # Sitemap & Robots
        res_sitemap = client.get('/sitemap.xml')
        with open(os.path.join(dist_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
            f.write(res_sitemap.data.decode('utf-8'))

        res_robots = client.get('/robots.txt')
        with open(os.path.join(dist_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
            f.write(res_robots.data.decode('utf-8'))

    # Netlify _redirects file for form handling / 404
    with open(os.path.join(dist_dir, '_redirects'), 'w', encoding='utf-8') as f:
        f.write("/* /index.html 200\n")

    print(f"Static site successfully built in: {dist_dir}")

if __name__ == '__main__':
    export_static_site()
