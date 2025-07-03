# chat/views/home.py
from django.http import HttpResponse
from django.urls import reverse


def home(request):
    links = {
        "API Docs (Swagger UI)": reverse("schema_swagger_ui"),
        "API Docs (Redoc UI)": reverse("schema_redoc"),
        "Admin Login": reverse("admin_login"),
        "User Admin Panel": reverse("user_admin_panel"),
        "API Router Root": reverse("room-list"),
    }

    html_links = "".join(
        f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></li>'
        for name, url in links.items()
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Chatbot API</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn&display=swap');

            body {{
                font-family: 'Vazirmatn', Tahoma, sans-serif;
                background: #eef2f7;
                margin: 0;
                padding: 2rem;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                direction: rtl;
            }}
            .container {{
                background: #fff;
                padding: 2rem 3rem;
                border-radius: 12px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                max-width: 480px;
                text-align: center;
            }}
            h1 {{
                color: #27ae60;
                margin-bottom: 1rem;
                font-weight: 700;
                font-size: 2.4rem;
            }}
            p {{
                color: #555;
                margin-bottom: 2rem;
                font-size: 1.1rem;
            }}
            ul {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            li {{
                margin: 0.8rem 0;
            }}
            a {{
                text-decoration: none;
                color: #2980b9;
                font-weight: 600;
                font-size: 1.1rem;
                transition: color 0.3s ease;
            }}
            a:hover {{
                color: #1c5980;
                text-decoration: underline;
            }}
            footer {{
                margin-top: 2rem;
                font-size: 0.9rem;
                color: #aaa;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ چت‌بات آماده به کار است!</h1>
            <p>به پنل مدیریت و مستندات API از طریق لینک‌های زیر دسترسی داشته باشید:</p>
            <ul>
                {html_links}
            </ul>
            <footer>© ۲۰۲۵ Chatbot API</footer>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
