import os
import shutil
import re
from app import app

def make_relative(html):
    html = html.replace('href="/static/', 'href="./static/')
    html = html.replace('src="/static/', 'src="./static/')
    html = html.replace('http://localhost/static/', './static/')
    html = html.replace('http://localhost:5000/static/', './static/')
    
    html = html.replace('href="/login"', 'href="login.html"')
    html = html.replace('href="/logout"', 'href="login.html"')
    html = html.replace('href="/admin/dashboard"', 'href="admin.html"')
    html = html.replace('href="/team/dashboard"', 'href="team.html"')
    html = html.replace('href="/partner/dashboard"', 'href="partner.html"')
    html = re.sub(r'href="/id-card/\d+"', 'href="id-card.html"', html)
    html = html.replace('href="/"', 'href="index.html"')
    html = html.replace('href="/#', 'href="index.html#')
    return html

def export_all():
    base_dir = os.path.dirname(__file__)
    dist_dir = os.path.join(base_dir, 'dist')
    docs_dir = os.path.join(base_dir, 'docs')

    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    pages = {}

    with app.test_client() as client:
        # 1. Home Page
        res = client.get('/')
        home_html = make_relative(res.data.decode('utf-8'))
        pages['index.html'] = home_html

        # 2. Login Page
        res_login = client.get('/login')
        login_html = make_relative(res_login.data.decode('utf-8'))
        pages['login.html'] = login_html

        # 3. Admin Dashboard
        client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        res_admin = client.get('/admin/dashboard')
        admin_html = make_relative(res_admin.data.decode('utf-8'))
        pages['admin.html'] = admin_html

        # 4. Team Dashboard
        client.get('/logout')
        client.post('/login', data={'username': 'team1', 'password': 'team123'})
        res_team = client.get('/team/dashboard')
        team_html = make_relative(res_team.data.decode('utf-8'))
        pages['team.html'] = team_html

        # 5. Partner Dashboard
        client.get('/logout')
        client.post('/login', data={'username': 'partner1', 'password': 'partner123'})
        res_partner = client.get('/partner/dashboard')
        partner_html = make_relative(res_partner.data.decode('utf-8'))
        pages['partner.html'] = partner_html

        # 6. ID Card Generator
        res_id = client.get('/id-card/1')
        id_html = make_relative(res_id.data.decode('utf-8'))
        pages['id-card.html'] = id_html

        # Save all generated pages to root, dist, and docs
        for filename, content in pages.items():
            for target_dir in [base_dir, dist_dir, docs_dir]:
                with open(os.path.join(target_dir, filename), 'w', encoding='utf-8') as f:
                    f.write(content)

        # Sitemap & Robots for all directories
        res_sitemap = client.get('/sitemap.xml')
        sitemap_content = res_sitemap.data.decode('utf-8')
        res_robots = client.get('/robots.txt')
        robots_content = res_robots.data.decode('utf-8')

        for target in [base_dir, dist_dir, docs_dir]:
            with open(os.path.join(target, 'sitemap.xml'), 'w', encoding='utf-8') as f:
                f.write(sitemap_content)
            with open(os.path.join(target, 'robots.txt'), 'w', encoding='utf-8') as f:
                f.write(robots_content)
            with open(os.path.join(target, '_redirects'), 'w', encoding='utf-8') as f:
                f.write("/* /index.html 200\n")

    # Ensure static assets are copied to dist and docs as well
    static_src = os.path.join(base_dir, 'static')
    for target in [dist_dir, docs_dir]:
        dest = os.path.join(target, 'static')
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(static_src, dest)

    print("Static export successfully built: index.html, login.html, admin.html, team.html, partner.html, id-card.html across root, dist/, and docs/!")

if __name__ == '__main__':
    export_all()
