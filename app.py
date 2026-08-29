import os
import io
import json
import base64
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Digital Ad Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Montserrat:wght@400;700;800&family=Outfit:wght@400;600;800&display=swap');
    
    /* Main Theme Variables */
    :root {
        --bg-color: #0f172a;
        --card-bg: #1e293b;
        --accent-purple: #8b5cf6;
        --accent-blue: #3b82f6;
        --text-primary: #f8fafc;
    }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #a855f7 0%, #3b82f6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-family: 'Inter', sans-serif;
        color: #94a3b8;
        font-size: 1.1rem;
    }
    
    /* Color Swatch Chip */
    .color-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #fff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .swatch-circle {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,0.4);
    }
    
    /* Canva Button Style */
    .canva-btn {
        display: inline-block;
        background: linear-gradient(135deg, #00c4cc 0%, #7d2ae8 100%);
        color: white !important;
        font-weight: 700;
        padding: 12px 24px;
        border-radius: 10px;
        text-decoration: none !important;
        text-align: center;
        width: 100%;
        box-shadow: 0 4px 15px rgba(125, 42, 232, 0.4);
        transition: transform 0.2s ease;
    }
    .canva-btn:hover {
        transform: translateY(-2px);
    }

    /* Live Ad Card Base */
    .ad-card-wrapper {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        position: relative;
    }
</style>
""", unsafe_allow_html=True)

# Helper: Google GenAI Client
def get_gemini_client(api_key: str):
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Google GenAI Client: {e}")
        return None# Fallback Gradient Image Generator (PIL)
def generate_gradient_fallback(colors: list, width: int = 800, height: int = 800) -> Image.Image:
    """Generates a smooth dual-color gradient image as visual fallback."""
    base = Image.new("RGB", (width, height), colors[0] if colors else "#0f172a")
    top = Image.new("RGB", (width, height), colors[1] if len(colors) > 1 else "#1e1b4b")
    
    mask = Image.new("L", (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            val = int(255 * ((x + y) / (width + height)))
            mask_data.append(val)
    mask.putdata(mask_data)
    
    gradient_img = Image.composite(top, base, mask)
    
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 3
    
    accent_hex = colors[2] if len(colors) > 2 else "#3b82f6"
    try:
        h = accent_hex.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        rgb = (59, 130, 246)
        
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=(rgb[0], rgb[1], rgb[2], 90)
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(60))
    
    final_img = Image.alpha_composite(gradient_img.convert("RGBA"), overlay)
    return final_img.convert("RGB")

# 1. Gemini Imagen 3 Generator
def generate_gemini_imagen(client, prompt: str, aspect_ratio_str: str = "1:1") -> Image.Image:
    """Generates high-resolution commercial product poster visuals using Gemini Imagen 3."""
    if not client:
        return None
        
    ar_map = {
        "Instagram Post (1:1 Square)": "1:1",
        "Facebook / LinkedIn Feed (1.91:1 Banner)": "16:9",
        "Twitter / X Header (3:1 Landscape)": "16:9",
        "Story / Mobile Vertical (9:16)": "9:16",
        "Web Display Banner (16:9)": "16:9"
    }
    target_ar = ar_map.get(aspect_ratio_str, "1:1")
    
    if types is not None:
        genai_types = types
    else:
        from google.genai import types as genai_types

    models_to_try = ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001"]
    for m in models_to_try:
        try:
            res = client.models.generate_images(
                model=m,
                prompt=prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=target_ar,
                    output_mime_type="image/jpeg"
                )
            )
            if res and res.generated_images and len(res.generated_images) > 0:
                img_bytes = res.generated_images[0].image.image_bytes
                if img_bytes:
                    return Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as e:
            print(f"Gemini Imagen error ({m}): {e}")
            continue
    return None

# 2. Pollinations AI Generator (Instant FLUX.1 Engine - Free)
def generate_pollinations_image(prompt: str, width: int = 800, height: int = 800) -> Image.Image:
    """Generates AI product visuals via Pollinations AI (FLUX.1)."""
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200 and len(response.content) > 1000:
            return Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"Pollinations AI error: {e}")
    return None

# 3. Hugging Face Inference API Generator
def generate_hf_image(prompt: str, hf_token: str, width: int = 800, height: int = 800) -> Image.Image:
    """Calls Hugging Face Inference API for FLUX.1-schnell."""
    if not hf_token:
        return None
        
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": min(width, 1024),
            "height": min(height, 1024)
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"Hugging Face API error: {e}")
    return None

# Multi-Engine Image Generator Dispatcher
def generate_ad_image(
    prompt: str, 
    client, 
    hf_token: str, 
    width: int = 800, 
    height: int = 800, 
    colors: list = None,
    platform: str = "Instagram Post (1:1 Square)",
    preferred_engine: str = "Gemini Imagen 3 (Default)"
) -> tuple[Image.Image, str]:
    """Multi-Engine AI Image Pipeline: Gemini Imagen 3 -> Pollinations AI -> Hugging Face -> Gradient Fallback."""
    
    # 1. Gemini Imagen 3 (Uses user's Gemini API key!)
    if preferred_engine in ["Auto (Best Available)", "Gemini Imagen 3 (Default)"] and client:
        img = generate_gemini_imagen(client, prompt, aspect_ratio_str=platform)
        if img:
            return img, "Gemini Imagen 3"
            
    # 2. Pollinations AI (FLUX.1 Engine)
    if preferred_engine in ["Auto (Best Available)", "Gemini Imagen 3 (Default)", "Pollinations AI (FLUX.1)"]:
        img = generate_pollinations_image(prompt, width=width, height=height)
        if img:
            return img, "Pollinations AI (FLUX.1)"

    # 3. Hugging Face FLUX
    if preferred_engine in ["Auto (Best Available)", "Hugging Face (FLUX)"] and hf_token:
        img = generate_hf_image(prompt, hf_token=hf_token, width=width, height=height)
        if img:
            return img, "Hugging Face (FLUX.1)"
            
    # 4. Gradient Fallback (If all network calls fail)
    return generate_gradient_fallback(colors or ["#0f172a", "#1e1b4b", "#6366f1"], width, height), "Gradient Backdrop"

# Gemini 3.6 Flash Structured Copy & Design Generator
def generate_ad_campaign(
    client, 
    product_name: str, 
    product_desc: str, 
    target_audience: str, 
    platform: str, 
    brand_tone: str,
    cta_focus: str
):
    if types is not None:
        genai_types = types
    else:
        from google.genai import types as genai_types
    
    system_prompt = """You are an elite Creative Director, Senior Copywriter, and Visual Designer at a world-class advertising agency.
Your task is to convert raw product information into a high-converting digital advertisement package tailored for a specific platform and target audience.

CRITICAL REQUIREMENT FOR THE BACKGROUND IMAGE PROMPT:
The "background_image_prompt" MUST be an ultra-detailed, photorealistic commercial product photography prompt for text-to-image AI generators (Gemini Imagen 3 / FLUX.1).
It MUST specifically describe:
1. The exact product prominently displayed in the center or hero position, showcasing its key design features, sleek textures, materials (e.g. metallic, matte glass, premium leather), and vibrant colors.
2. Professional studio commercial photography environment (e.g. sleek dark pedestal/podium, floating dynamic elements, soft studio rim lighting, cinematic depth of field, dramatic shadows).
3. Aesthetic visual mood matching the brand tone (e.g. cyberpunk neon lights, ultra-clean minimalism, luxury metallic accents).
4. DO NOT include any text, letters, or words in the background_image_prompt itself.

You MUST respond strictly with a valid JSON object following this exact schema:
{
  "headline": "Punchy, attention-grabbing primary headline (3-8 words)",
  "subheadline": "Engaging subheadline driving value proposition (10-20 words)",
  "cta": "Strong call to action text (e.g. 'Shop 20% Off Today', 'Get Instant Access')",
  "background_image_prompt": "Ultra-detailed commercial studio product shot of [Product Name], featuring [key visual details], resting on a sleek dark display podium, cinematic studio lighting, dramatic rim light reflections, elegant depth of field, luxury ad aesthetic, 8k resolution.",
  "color_palette": {
    "primary": "#HEXCODE",
    "secondary": "#HEXCODE",
    "accent": "#HEXCODE",
    "text": "#HEXCODE",
    "background": "#HEXCODE"
  },
  "color_names": {
    "primary": "Descriptive color name",
    "secondary": "Descriptive color name",
    "accent": "Descriptive color name"
  },
  "font_pairing": {
    "header": "Google Font Name (e.g., Montserrat, Outfit, Playfair Display)",
    "body": "Google Font Name (e.g., Inter, Roboto, Open Sans)"
  },
  "target_emotion": "Core psychological emotion triggered (e.g. FOMO, Empowerment, Prestige, Ease)",
  "copywriting_angle": "Short strategy breakdown of why this copy converts",
  "canva_template_keywords": ["keyword1", "keyword2", "keyword3"]
}"""

    user_prompt = f"""
Product Name: {product_name}
Description / Features: {product_desc}
Target Audience: {target_audience}
Platform Format: {platform}
Brand Tone / Vibe: {brand_tone}
CTA Focus / Goal: {cta_focus}
"""

    # Primary model gemini-3.6-flash with fallbacks for maximum compatibility across API keys
    candidate_models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    last_exception = None
    
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            return json.loads(response.text)
        except Exception as e:
            last_exception = e
            if "404" in str(e) or "NOT_FOUND" in str(e):
                continue
            raise e
            
    if last_exception:
        raise last_exception

# Pillow Composite Ad Generator for High-Res PNG Download
def create_composite_ad(
    bg_image: Image.Image,
    ad_data: dict,
    width: int,
    height: int,
    layout_style: str = "Modern Overlay"
) -> Image.Image:
    """Renders copy, styling overlays, and CTA button directly onto the background image using Pillow."""
    # Resize background image to standard output dimensions
    canvas = bg_image.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
    
    # Create dark gradient overlay for legibility
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    if layout_style == "Modern Overlay":
        # Bottom half gradient overlay
        for y in range(int(height * 0.35), height):
            alpha = int(220 * ((y - height * 0.35) / (height * 0.65)))
            draw.line([(0, y), (width, y)], fill=(15, 23, 42, alpha))
    elif layout_style == "Split Card":
        # Left side panel
        panel_width = int(width * 0.55)
        draw.rectangle([0, 0, panel_width, height], fill=(15, 23, 42, 230))
    else: # Full Dark Tint
        draw.rectangle([0, 0, width, height], fill=(15, 23, 42, 160))
        
    canvas = Image.alpha_composite(canvas, overlay)
    draw_final = ImageDraw.Draw(canvas)
    
    # Text rendering using standard default/fallback fonts
    headline = ad_data.get("headline", "")
    subheadline = ad_data.get("subheadline", "")
    cta = ad_data.get("cta", "SHOP NOW")
    
    # Parse color
    accent_hex = ad_data.get("color_palette", {}).get("accent", "#3b82f6")
    try:
        h = accent_hex.lstrip('#')
        accent_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent_rgb = (59, 130, 246)
        
    # Draw simple headline, subheadline & CTA button overlay
    # Using PIL default font scaled up gracefully or basic lines
    try:
        # Load a default PIL font or truetype if available
        font_head = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    except Exception:
        font_head = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Draw Badge
    draw_final.rectangle([40, 40, 180, 75], fill=(*accent_rgb, 200))
    draw_final.text((55, 50), "SPONSORED", fill=(255, 255, 255), font=font_sub)
    
    # Position text near bottom or split
    if layout_style == "Split Card":
        text_x = 40
        start_y = int(height * 0.25)
    else:
        text_x = 40
        start_y = int(height * 0.55)
        
    draw_final.text((text_x, start_y), headline.upper(), fill=(255, 255, 255), font=font_head)
    draw_final.text((text_x, start_y + 40), subheadline, fill=(203, 213, 225), font=font_sub)
    
    # CTA Button Box
    btn_y = start_y + 110
    draw_final.rectangle([text_x, btn_y, text_x + 220, btn_y + 45], fill=(*accent_rgb, 255))
    draw_final.text((text_x + 20, btn_y + 15), cta.upper(), fill=(255, 255, 255), font=font_sub)
    
    return canvas.convert("RGB")


# Main Application Layout
def main():
    # Header Banner
    st.markdown("""
    <div class="header-container">
        <div class="header-title">⚡ AI Digital Advertisement Generator</div>
        <div class="header-subtitle">Create high-converting ad copy, color palettes, and AI visuals powered by Gemini 3.6 & FLUX</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("🔑 API Credentials")
        
        env_gemini = os.getenv("GEMINI_API_KEY", "")
        env_hf = os.getenv("HF_TOKEN", "") or os.getenv("HF_API_KEY", "")
        
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=env_gemini,
            type="password",
            help="Free key from https://aistudio.google.com/app/apikey"
        )
        
        hf_token = st.text_input(
            "Hugging Face Token (Optional)",
            value=env_hf,
            type="password",
            help="Free token from https://huggingface.co/settings/tokens (for FLUX.1 AI images)"
        )
        
        st.divider()
        st.header("🎯 Ad Campaign Requirements")
        
        product_name = st.text_input("Product / Service Name", value="LuminoSound Pro", placeholder="e.g. UltraFit Smartwatch")
        
        product_desc = st.text_area(
            "Product Description & Key Features",
            value="Wireless noise-canceling headphones with 40-hour battery life, spatial audio, hyper-comfortable memory foam earcups, and sleek matte finish.",
            height=110
        )
        
        target_audience = st.selectbox(
            "Target Audience",
            [
                "Tech Enthusiasts & Creators",
                "Students & Young Professionals",
                "Fitness & Athletes",
                "Corporate Executives",
                "Gamers & Streamers",
                "Custom / Other"
            ]
        )
        if target_audience == "Custom / Other":
            target_audience = st.text_input("Specify Target Audience", value="Remote workers & digital nomads")
            
        platform = st.selectbox(
            "Ad Format / Platform",
            [
                "Instagram Post (1:1 Square)",
                "Facebook / LinkedIn Feed (1.91:1 Banner)",
                "Twitter / X Header (3:1 Landscape)",
                "Story / Mobile Vertical (9:16)",
                "Web Display Banner (16:9)"
            ]
        )
        
        brand_tone = st.selectbox(
            "Brand Style / Tone",
            [
                "Futuristic & Cyberpunk",
                "Minimalist & Clean",
                "Bold & Energetic",
                "Luxury & Premium",
                "Professional & Authoritative",
                "Fun & Playful"
            ]
        )
        
        cta_focus = st.selectbox(
            "Call-to-Action Goal",
            [
                "Direct Sale (e.g. 'Shop Now - 20% Off')",
                "Free Trial / Signup",
                "Lead Generation / Learn More",
                "Limited Time Urgency"
            ]
        )
        
        preferred_engine = st.selectbox(
            "🎨 Image Generation Engine",
            [
                "Gemini Imagen 3 (Default)",
                "Pollinations AI (FLUX.1)",
                "Hugging Face (FLUX)",
                "Auto (Best Available)"
            ],
            help="Choose which AI model generates the product background imagery."
        )
        
        st.divider()
        generate_btn = st.button("🚀 Generate AI Ad Campaign", use_container_width=True, type="primary")

    # Main Content Area
    if not gemini_api_key:
        st.warning("👈 Please enter your **Gemini API Key** in the sidebar to get started!")
        st.info("""
        ### 📌 Quick Setup Guide:
        1. Get a **Free Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey).
        2. Paste it in the sidebar field or set `GEMINI_API_KEY` in your `.env` file.
        3. **Gemini Imagen 3** is automatically used for AI poster visual generation with your Gemini API key!
        4. *(Optional)* Add a free **Hugging Face Token** from [Hugging Face Settings](https://huggingface.co/settings/tokens) if you prefer FLUX.1.
        """)
        return

    # Store state for ad campaign
    if "ad_package" not in st.session_state:
        st.session_state.ad_package = None
    if "bg_image" not in st.session_state:
        st.session_state.bg_image = None
    if "img_source" not in st.session_state:
        st.session_state.img_source = None

    # Handle Generation Trigger
    if generate_btn:
        with st.spinner("🤖 Calling Gemini 3.6 Flash to craft ad copy, visual prompt & design system..."):
            client = get_gemini_client(gemini_api_key)
            if not client:
                return
            try:
                ad_data = generate_ad_campaign(
                    client, product_name, product_desc, target_audience, platform, brand_tone, cta_focus
                )
                st.session_state.ad_package = ad_data
            except Exception as e:
                st.error(f"❌ Failed to generate ad campaign with Gemini: {e}")
                return

        # Determine canvas dimensions based on platform selection
        dims = {
            "Instagram Post (1:1 Square)": (800, 800),
            "Facebook / LinkedIn Feed (1.91:1 Banner)": (955, 500),
            "Twitter / X Header (3:1 Landscape)": (900, 300),
            "Story / Mobile Vertical (9:16)": (540, 960),
            "Web Display Banner (16:9)": (960, 540)
        }
        w, h = dims.get(platform, (800, 800))

        # Extract colors for fallback or styling
        colors = [
            st.session_state.ad_package.get("color_palette", {}).get("primary", "#0f172a"),
            st.session_state.ad_package.get("color_palette", {}).get("secondary", "#1e1b4b"),
            st.session_state.ad_package.get("color_palette", {}).get("accent", "#3b82f6")
        ]

        with st.spinner(f"🎨 Generating AI product visual using {preferred_engine}..."):
            img_prompt = st.session_state.ad_package.get("background_image_prompt", product_name)
            img, source = generate_ad_image(
                prompt=img_prompt,
                client=client,
                hf_token=hf_token,
                width=w,
                height=h,
                colors=colors,
                platform=platform,
                preferred_engine=preferred_engine
            )
            st.session_state.bg_image = img
            st.session_state.img_source = source
            st.toast(f"✅ AI Ad Campaign successfully generated via {source}!", icon="🎉")

    # Display Ad Results Dashboard
    if st.session_state.ad_package and st.session_state.bg_image:
        ad = st.session_state.ad_package
        bg_img = st.session_state.bg_image
        palette = ad.get("color_palette", {})
        color_names = ad.get("color_names", {})
        fonts = ad.get("font_pairing", {})

        # Top Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🖼️ Live Ad Preview & Layouts", 
            "✍️ Ad Copy & Strategy", 
            "🎨 Color & Typography System", 
            "🚀 Export & Direct Actions"
        ])

        # TAB 1: LIVE AD PREVIEW
        with tab1:
            st.subheader("Live Ad Visual Preview")
            
            col_preview, col_controls = st.columns([2, 1])
            
            with col_controls:
                st.markdown("#### ⚙️ Layout & Image Controls")
                
                st.success(f"🎨 Image Source: **{st.session_state.get('img_source', 'AI Engine')}**")
                
                layout_style = st.radio(
                    "Select Visual Layout Variant:",
                    ["Modern Overlay", "Split Card", "Full Tint Canvas"],
                    help="Switch between different visual overlay arrangements"
                )
                
                badge_text = st.text_input("Badge / Tagline", value="NEW ARRIVAL")
                
                dims = {
                    "Instagram Post (1:1 Square)": (800, 800),
                    "Facebook / LinkedIn Feed (1.91:1 Banner)": (955, 500),
                    "Twitter / X Header (3:1 Landscape)": (900, 300),
                    "Story / Mobile Vertical (9:16)": (540, 960),
                    "Web Display Banner (16:9)": (960, 540)
                }
                w, h = dims.get(platform, (800, 800))
                colors = [palette.get("primary", "#0f172a"), palette.get("secondary", "#1e1b4b"), palette.get("accent", "#3b82f6")]
                
                if st.button("🔄 Regenerate Background Image", use_container_width=True):
                    with st.spinner("🎨 Re-generating AI visual..."):
                        client = get_gemini_client(gemini_api_key)
                        img_prompt = ad.get("background_image_prompt", product_name)
                        new_img, new_src = generate_ad_image(
                            prompt=img_prompt,
                            client=client,
                            hf_token=hf_token,
                            width=w,
                            height=h,
                            colors=colors,
                            platform=platform,
                            preferred_engine=preferred_engine
                        )
                        st.session_state.bg_image = new_img
                        st.session_state.img_source = new_src
                        st.rerun()

                st.info(f"**Target Audience:** {target_audience}\n\n**Emotional Hook:** {ad.get('target_emotion', 'High Value')}")

            with col_preview:
                # Convert PIL image to base64 for HTML rendering
                buffered = io.BytesIO()
                bg_img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                # Extract palette variables
                primary_color = palette.get("primary", "#0f172a")
                accent_color = palette.get("accent", "#3b82f6")
                text_color = palette.get("text", "#ffffff")
                bg_color = palette.get("background", "#1e293b")
                
                header_font = fonts.get("header", "Outfit")
                body_font = fonts.get("body", "Inter")
                
                # HTML Live Interactive Preview Component
                html_code = f"""
                <link href="https://fonts.googleapis.com/css2?family={header_font.replace(' ', '+')}:wght@700;800&family={body_font.replace(' ', '+')}:wght@400;600&display=swap" rel="stylesheet">
                
                <div class="ad-card-wrapper" style="
                    background-image: url('data:image/png;base64,{img_str}');
                    background-size: cover;
                    background-position: center;
                    min-height: 480px;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-end;
                    position: relative;
                    font-family: '{body_font}', sans-serif;
                ">
                    <!-- Gradient overlay scrim -->
                    <div style="
                        position: absolute;
                        top: 0; left: 0; right: 0; bottom: 0;
                        background: {'linear-gradient(to right, rgba(15,23,42,0.95) 0%, rgba(15,23,42,0.6) 60%, rgba(0,0,0,0) 100%)' if layout_style == 'Split Card' else 'linear-gradient(to top, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.4) 50%, rgba(0,0,0,0.1) 100%)'};
                        z-index: 1;
                    "></div>
                    
                    <!-- Content Card Overlay -->
                    <div style="position: relative; z-index: 2; padding: 2.5rem; max-width: {'60%' if layout_style == 'Split Card' else '100%'};">
                        <span style="
                            background: {accent_color};
                            color: #ffffff;
                            font-size: 0.75rem;
                            font-weight: 800;
                            letter-spacing: 1.5px;
                            padding: 4px 12px;
                            border-radius: 20px;
                            text-transform: uppercase;
                            display: inline-block;
                            margin-bottom: 1rem;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                        ">{badge_text}</span>
                        
                        <h1 style="
                            font-family: '{header_font}', sans-serif;
                            color: {text_color};
                            font-size: 2.2rem;
                            font-weight: 800;
                            line-height: 1.2;
                            margin: 0 0 0.8rem 0;
                            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
                        ">{ad.get('headline', '')}</h1>
                        
                        <p style="
                            color: #e2e8f0;
                            font-size: 1.05rem;
                            line-height: 1.5;
                            margin: 0 0 1.5rem 0;
                            text-shadow: 0 1px 5px rgba(0,0,0,0.5);
                        ">{ad.get('subheadline', '')}</p>
                        
                        <div style="
                            display: inline-block;
                            background: {accent_color};
                            color: #ffffff;
                            font-family: '{header_font}', sans-serif;
                            font-weight: 700;
                            font-size: 1rem;
                            padding: 12px 28px;
                            border-radius: 8px;
                            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        ">{ad.get('cta', 'Shop Now')} →</div>
                    </div>
                </div>
                """
                st.components.v1.html(html_code, height=520, scrolling=False)

        # TAB 2: AD COPY & STRATEGY
        with tab2:
            st.subheader("✍️ High-Converting Copywriter Script")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Primary Headline")
                st.code(ad.get("headline", ""), language="text")
                
                st.markdown("#### Subheadline / Body Copy")
                st.code(ad.get("subheadline", ""), language="text")
                
                st.markdown("#### Call To Action (CTA)")
                st.code(ad.get("cta", ""), language="text")

            with c2:
                st.markdown("#### 🎯 Copywriting Strategy Angle")
                st.info(ad.get("copywriting_angle", "Targeted psychological hook."))
                
                st.markdown("#### 🖼️ AI Image Prompt Visual Concept")
                st.code(ad.get("background_image_prompt", ""), language="text")

        # TAB 3: COLOR & TYPOGRAPHY
        with tab3:
            st.subheader("🎨 Brand Design System")
            
            st.markdown("#### Recommended Color Palette")
            palette_html = ""
            for key in ["primary", "secondary", "accent", "background", "text"]:
                hex_val = palette.get(key, "#ffffff")
                c_name = color_names.get(key, key.capitalize())
                palette_html += f"""
                <div class="color-chip" style="background-color: #1e293b;">
                    <div class="swatch-circle" style="background-color: {hex_val};"></div>
                    <span><b>{key.capitalize()}:</b> {hex_val} ({c_name})</span>
                </div>
                """
            st.markdown(f"<div>{palette_html}</div>", unsafe_allow_html=True)
            
            st.divider()
            st.markdown("#### 🔤 Typography Recommendation")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown(f"**Header Font:** `{fonts.get('header', 'Montserrat')}`")
                st.caption("Ideal for bold headlines, primary badges, and high-impact text.")
            with col_f2:
                st.markdown(f"**Body Font:** `{fonts.get('body', 'Inter')}`")
                st.caption("Optimized for clean legibility across mobile screens and ad cards.")

        # TAB 4: EXPORT & ACTIONS
        with tab4:
            st.subheader("🚀 Export Assets & External Integrations")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                st.markdown("### 📥 Download PNG Ad Image")
                st.write("Generates a flattened, high-resolution composite PNG image complete with text overlays, scrims, and CTA button.")
                
                # Render composite PIL image
                composite_img = create_composite_ad(
                    bg_img, ad, width=800, height=800, layout_style=layout_style
                )
                
                buf = io.BytesIO()
                composite_img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="⬇️ Download Flattened Ad PNG",
                    data=byte_im,
                    file_name=f"{product_name.lower().replace(' ', '_')}_ad.png",
                    mime="image/png",
                    use_container_width=True,
                    type="primary"
                )

            with col_exp2:
                st.markdown("### 🎨 Edit Directly in Canva")
                st.write("Launch Canva's graphic editor with pre-filled search templates for your ad style.")
                
                canva_keywords = "+".join(ad.get("canva_template_keywords", [product_name, brand_tone, "ad"]))
                canva_url = f"https://www.canva.com/search?q={canva_keywords}+ad+template"
                
                st.markdown(
                    f'<a href="{canva_url}" target="_blank" class="canva-btn">✨ Open & Edit in Canva</a>',
                    unsafe_allow_html=True
                )
                
            st.divider()
            st.markdown("### 📋 Copy Campaign JSON Payload")
            st.json(ad)

if __name__ == "__main__":
    main()
