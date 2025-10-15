# app/main.py
import os
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv
from app.models import GenerateRequest
from app.generator import SiteGenerator

load_dotenv()
SITES_DIR = os.getenv("SITES_DIR", "./sites")

app = FastAPI(
    title="LLM Site Generator",
    description="Generate AI-powered websites with various styles",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = SiteGenerator()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Служить фронтенд інтерфейс"""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend.html")
    
    # Якщо файл існує, повертаємо його
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # Якщо файлу немає, повертаємо вбудований HTML
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>AI Site Generator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .card {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #667eea; }
            .info { margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 5px; }
            a { color: #667eea; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 AI Site Generator API</h1>
            <div class="info">
                <p><strong>Frontend not found!</strong></p>
                <p>Create <code>app/frontend.html</code> file or use the API directly.</p>
            </div>
            <h2>API Endpoints:</h2>
            <ul>
                <li><a href="/docs">📖 API Documentation (Swagger)</a></li>
                <li><a href="/ping">🏓 Ping (Health Check)</a></li>
                <li><a href="/logs">📋 View Logs</a></li>
            </ul>
            <h2>Quick Start:</h2>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">
curl -X POST "http://127.0.0.1:8000/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "Machine Learning",
    "pages_count": 1,
    "style": "educational",
    "generate_image": false
  }'
            </pre>
        </div>
    </body>
    </html>
    """)

@app.get("/ping")
async def ping():
    """Перевірка статусу API"""
    return {"status": "ok", "message": "API is running"}

@app.post("/generate")
async def generate(req: GenerateRequest):
    """Генерує сайти на основі запиту"""
    items = await generator.generate_sites(req)
    return items

@app.get("/site/{site_id}")
async def get_site(site_id: str):
    """Отримує згенерований сайт за ID"""
    path = generator.get_site_path(site_id)
    if not path:
        raise HTTPException(status_code=404, detail="Site not found")
    with open(path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")

@app.get("/image/{filename}")
async def get_image(filename: str):
    """Отримує зображення за назвою файлу"""
    # Перевірка безпеки: дозволяємо тільки image_ файли
    if not filename.startswith("image_") or not filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid image filename")
    
    image_path = os.path.join(SITES_DIR, filename)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
    return FileResponse(image_path, media_type="image/png")

@app.get("/logs")
async def logs():
    """Повертає всі логи генерації"""
    return generator.get_logs()

@app.get("/stats")
async def stats():
    """Статистика використання"""
    logs = generator.get_logs()
    
    # Підрахунок статистики
    total_sites = len([log for log in logs if log.get("site_id")])
    styles_count = {}
    topics_count = {}
    
    for log in logs:
        style = log.get("style")
        topic = log.get("topic")
        
        if style:
            styles_count[style] = styles_count.get(style, 0) + 1
        if topic:
            topics_count[topic] = topics_count.get(topic, 0) + 1
    
    return {
        "total_sites": total_sites,
        "total_requests": len(logs),
        "styles_distribution": styles_count,
        "popular_topics": dict(sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:10])
    }