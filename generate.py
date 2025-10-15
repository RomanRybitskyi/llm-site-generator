# generate.py
import argparse
import asyncio
from app.models import GenerateRequest
from app.generator import SiteGenerator

parser = argparse.ArgumentParser(
    description="Generate AI-powered websites from command line"
)
parser.add_argument("--topic", required=True, help="Topic for website generation")
parser.add_argument("--count", type=int, default=1, help="Number of pages to generate")
parser.add_argument("--style", default="educational", 
                   choices=["educational", "marketing", "technical", "minimalist", "creative", "casual"],
                   help="Content style")
parser.add_argument("--temperature", type=float, default=0.8,
                   help="Temperature for LLM (0.1-1.5)")
parser.add_argument("--randomize-temp", action="store_true",
                   help="Randomize temperature for each generation")
parser.add_argument("--temp-min", type=float, default=0.5,
                   help="Minimum temperature when randomizing")
parser.add_argument("--temp-max", type=float, default=1.2,
                   help="Maximum temperature when randomizing")
parser.add_argument("--no-image", action="store_true",
                   help="Skip image generation")
parser.add_argument("--max-tokens", type=int, default=1200,
                   help="Maximum tokens for generation")

args = parser.parse_args()

async def main():
    print(f"🚀 Starting generation...")
    print(f"📋 Topic: {args.topic}")
    print(f"📊 Count: {args.count}")
    print(f"🎨 Style: {args.style}")
    
    if args.randomize_temp:
        print(f"🎲 Random temperature: {args.temp_min} - {args.temp_max}")
    else:
        print(f"🌡️  Fixed temperature: {args.temperature}")
    
    gen = SiteGenerator()
    req = GenerateRequest(
        topic=args.topic,
        pages_count=args.count,
        style=args.style,
        temperature=args.temperature,
        randomize_temperature=args.randomize_temp,
        temperature_min=args.temp_min,
        temperature_max=args.temp_max,
        generate_image=not args.no_image,
        max_tokens=args.max_tokens
    )
    
    res = await gen.generate_sites(req)
    
    print("\n✅ Generation completed!")
    print(f"📁 Generated {len(res)} site(s):\n")
    
    for i, site in enumerate(res, 1):
        print(f"{i}. {site['title']}")
        print(f"   ID: {site['site_id']}")
        if 'temperature_used' in site:
            print(f"   🌡️  Temperature: {site['temperature_used']}")
        print(f"   📄 File: {site['file_path']}")
        print()

if __name__ == "__main__":
    asyncio.run(main())