import os
import shutil
import re
from app import app

def export_all():
    base_dir = os.path.dirname(__file__)
    dist_dir = os.path.join(base_dir, 'dist')
    docs_dir = os.path.join(base_dir, 'docs')

    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    # Render pages with test client
    with app.test_client() as client:
        res = client.get('/')
        html = res.data.decode('utf-8')

        # Replace all absolute paths with relative paths for GitHub Pages subfolder compatibility
        html = html.replace('href="/static/', 'href="./static/')
        html = html.replace('src="/static/', 'src="./static/')
        html = html.replace('href="/"', 'href="./"')
        html = html.replace('href="/#', 'href="#')
        html = html.replace('http://localhost/static/', './static/')
        html = html.replace('href="/login"', 'href="#contact"')  # On static site, link login/portal to contact/login note

        # Enhance static form so it works seamlessly on static hosting (Netlify & GitHub Pages):
        # On static hosting, send via WhatsApp & Netlify Form
        form_enhancement = '''<form name="project-enquiry" method="POST" data-netlify="true" onsubmit="event.preventDefault(); var n=this.name.value; var p=this.phone.value; var s=this.service.value; var m=this.message.value; window.open('https://wa.me/919005874417?text=' + encodeURIComponent('New Project Requirement from ' + n + ' (' + p + ') for ' + s + ': ' + m), '_blank'); alert('Thank you! Opening WhatsApp to connect directly with the Technical Lead.');" class="space-y-3">
        <input type="hidden" name="form-name" value="project-enquiry" />'''
        html = re.sub(r'<form action="/enquire"[^>]*class="space-y-3">', form_enhancement, html)

        # 1. Save to root index.html (Allows Netlify to deploy directly from root with 0 configuration!)
        root_index = os.path.join(base_dir, 'index.html')
        with open(root_index, 'w', encoding='utf-8') as f:
            f.write(html)

        # 2. Save to dist/index.html (For Netlify publish directory dist)
        dist_index = os.path.join(dist_dir, 'index.html')
        with open(dist_index, 'w', encoding='utf-8') as f:
            f.write(html)

        # 3. Save to docs/index.html (For GitHub Pages /docs)
        docs_index = os.path.join(docs_dir, 'index.html')
        with open(docs_index, 'w', encoding='utf-8') as f:
            f.write(html)

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

    # Ensure static folder is copied to dist and docs as well
    static_src = os.path.join(base_dir, 'static')
    for target in [dist_dir, docs_dir]:
        dest = os.path.join(target, 'static')
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(static_src, dest)

    print("Static build complete for Root, docs/, and dist/!")

if __name__ == '__main__':
    export_all()
