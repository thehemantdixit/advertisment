import os
import io
import json
import base64
import random
import datetime as dt
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


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="Adgen — AI Ad Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "job_number" not in st.session_state:
    st.session_state.job_number = random.randint(100, 999)

# ---------------------------------------------------------------------------
# Theme
#
# Direction: Adgen reads as a confident, contemporary creative tool rather
# than a generic AI wrapper — warm paper surface, one loud coral-red working
# accent, soft rounded cards with real elevation, and a display/mono type
# pairing that feels like a design studio's internal tool. Every native
# Streamlit widget (inputs, selects, alerts, expanders) is re-skinned so
# nothing reverts to Streamlit's default dark widget chrome on a light page.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg: #0b0d12;
        --bg-2: #10131a;
        --panel: rgba(20, 23, 31, 0.88);
        --panel-solid: #151922;
        --panel-soft: #1b1f29;
        --border: rgba(255,255,255,0.09);
        --border-strong: rgba(255,255,255,0.16);
        --text: #f6f7fb;
        --muted: #9aa1b2;
        --muted-2: #70788b;
        --accent: #ff4f6d;
        --accent-2: #ff8a5b;
        --cyan: #55d6ff;
        --success: #61e294;
        --shadow: 0 20px 60px rgba(0,0,0,.28);
        --glow: 0 0 35px rgba(255,79,109,.16);
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--text);
    }

    .stApp {
        background:
            radial-gradient(circle at 78% 8%, rgba(255,79,109,.11), transparent 24%),
            radial-gradient(circle at 20% 82%, rgba(85,214,255,.07), transparent 22%),
            linear-gradient(135deg, var(--bg) 0%, #0d1017 52%, #0a0c11 100%);
    }

    .main .block-container {
        max-width: 1450px;
        padding: 2.2rem 3rem 4rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(18,21,29,.98), rgba(10,12,17,.98));
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.3rem;
    }

    section[data-testid="stSidebar"] * {
        color: var(--text);
    }

    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--muted);
    }

    section[data-testid="stSidebar"] hr {
        border-color: var(--border);
    }

    /* Typography */
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.035em;
        color: var(--text) !important;
    }

    p, label, .stCaption, small {
        color: var(--muted);
    }

    /* Top header */
    .ticket-strip {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: .2rem 0 1.25rem;
    }

    .wordmark {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.25rem;
        font-weight: 700;
        letter-spacing: -.07em;
        line-height: .9;
        color: #fff;
    }

    .wordmark span {
        color: var(--accent);
        text-shadow: 0 0 22px rgba(255,79,109,.55);
    }

    .wordmark-sub {
        display: block;
        margin-top: .65rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: .67rem;
        letter-spacing: .13em;
        text-transform: uppercase;
        color: var(--muted-2);
    }

    .ticket-right {
        text-align: right;
        font-family: 'JetBrains Mono', monospace;
        color: var(--muted-2);
        font-size: .7rem;
        line-height: 1.8;
        letter-spacing: .08em;
    }

    .ticket-right b {
        color: var(--accent);
        font-size: .95rem;
    }

    .ticket-rule {
        height: 1px;
        border: 0;
        margin: 0 0 1.8rem;
        background: linear-gradient(90deg, var(--accent), rgba(255,79,109,.15), transparent);
    }

    /* Section labels */
    .brief-eyebrow {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: .68rem;
        font-weight: 600;
        letter-spacing: .16em;
        text-transform: uppercase;
        color: var(--accent);
        margin: 1.3rem 0 .9rem;
    }

    .brief-eyebrow::before {
        content: '';
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 15px rgba(255,79,109,.7);
    }

    /* Cards / forms */
    div[data-testid="stForm"],
    div[data-testid="stExpander"] {
        background: linear-gradient(145deg, rgba(24,28,38,.96), rgba(15,18,25,.96)) !important;
        border: 1px solid var(--border) !important;
        border-radius: 22px !important;
        box-shadow: var(--shadow) !important;
    }

    div[data-testid="stForm"] {
        padding: 1.7rem 1.7rem 1.25rem !important;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 600;
    }

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background: rgba(255,255,255,.045) !important;
        color: var(--text) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 13px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
        transition: all .18s ease;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stNumberInput input::placeholder {
        color: #687083 !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus {
        border-color: rgba(255,79,109,.8) !important;
        box-shadow: 0 0 0 3px rgba(255,79,109,.12), var(--glow) !important;
    }

    div[data-baseweb="select"] > div {
        background: rgba(255,255,255,.045) !important;
        color: var(--text) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 13px !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: var(--text) !important;
    }

    ul[data-baseweb="menu"],
    div[data-baseweb="popover"] {
        background: #171b24 !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 13px !important;
    }

    ul[data-baseweb="menu"] li {
        color: var(--text) !important;
    }

    ul[data-baseweb="menu"] li:hover {
        background: rgba(255,79,109,.12) !important;
    }

    .stRadio label,
    .stCheckbox label,
    .stSelectbox label,
    .stTextInput label,
    .stTextArea label,
    .stNumberInput label {
        color: var(--muted) !important;
        font-size: .78rem !important;
        font-weight: 600 !important;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        min-height: 44px;
        border-radius: 13px !important;
        border: 1px solid var(--border-strong) !important;
        background: rgba(255,255,255,.055) !important;
        color: var(--text) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: .01em !important;
        box-shadow: 0 8px 25px rgba(0,0,0,.16) !important;
        transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(255,255,255,.28) !important;
        background: rgba(255,255,255,.09) !important;
        box-shadow: 0 14px 35px rgba(0,0,0,.25) !important;
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
        border-color: transparent !important;
        color: white !important;
        box-shadow: 0 12px 32px rgba(255,79,109,.22) !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        filter: brightness(1.07);
        box-shadow: 0 17px 40px rgba(255,79,109,.32) !important;
    }

    /* Alerts */
    div[data-testid="stAlert"],
    .stAlert {
        border-radius: 16px !important;
        border: 1px solid rgba(255,193,7,.18) !important;
        background: rgba(255,193,7,.07) !important;
        color: #f5df9a !important;
    }

    div[data-testid="stAlert"] *,
    .stAlert * {
        color: inherit !important;
    }

    /* Tabs */
    div[data-baseweb="tab-list"] {
        gap: 7px;
        background: rgba(255,255,255,.025);
        border: 1px solid var(--border);
        padding: 6px;
        border-radius: 16px;
    }

    button[data-baseweb="tab"] {
        border-radius: 11px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: .66rem !important;
        letter-spacing: .05em;
        text-transform: uppercase;
        color: var(--muted) !important;
        padding: 10px 14px !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #fff !important;
        background: rgba(255,79,109,.13) !important;
    }

    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Preview */
    .ad-card-wrapper {
        border: 1px solid var(--border-strong);
        border-radius: 22px;
        overflow: hidden;
        margin-top: .5rem;
        margin-bottom: 1rem;
        position: relative;
        box-shadow: 0 25px 70px rgba(0,0,0,.35);
    }

    .proof-stamp {
        position: absolute;
        top: 15px;
        right: 15px;
        z-index: 3;
        background: rgba(8,10,14,.62);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,.18);
        color: #fff;
        font-family: 'JetBrains Mono', monospace;
        font-size: .58rem;
        letter-spacing: .09em;
        text-transform: uppercase;
        padding: 7px 10px;
        border-radius: 999px;
    }

    /* Color chips */
    .color-chip {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        padding: 8px 12px;
        margin: 4px 5px 4px 0;
        border: 1px solid var(--border);
        background: rgba(255,255,255,.035);
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: .65rem;
        color: var(--muted);
    }

    .swatch-circle {
        width: 15px;
        height: 15px;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,.25);
        box-shadow: 0 0 10px rgba(255,255,255,.08);
    }

    /* Code blocks */
    div[data-testid="stCode"] {
        border-radius: 14px !important;
        border: 1px solid var(--border) !important;
    }

    /* Dividers */
    hr {
        border-color: var(--border) !important;
    }

    /* Captions */
    [data-testid="stCaptionContainer"] {
        color: var(--muted-2) !important;
    }

    /* Sidebar engine select */
    section[data-testid="stSidebar"] .stSelectbox {
        margin-bottom: .2rem;
    }

    /* Canva button */
    .canva-btn {
        display: block;
        padding: 13px 18px;
        border-radius: 13px;
        text-decoration: none !important;
        text-align: center;
        background: linear-gradient(135deg, rgba(255,79,109,.14), rgba(85,214,255,.08));
        color: #fff !important;
        border: 1px solid var(--border-strong);
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        transition: all .16s ease;
    }

    .canva-btn:hover {
        transform: translateY(-2px);
        border-color: rgba(255,79,109,.55);
        box-shadow: 0 12px 30px rgba(0,0,0,.22);
    }

    /* Mobile */
    @media (max-width: 900px) {
        .main .block-container {
            padding: 1.2rem 1rem 3rem;
        }

        .wordmark {
            font-size: 2.45rem;
        }

        .ticket-right {
            font-size: .6rem;
        }

        div[data-baseweb="tab-list"] {
            overflow-x: auto;
        }
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Gemini / image-engine plumbing (unchanged behaviour, same three engines)
# ---------------------------------------------------------------------------
def get_gemini_client(api_key: str):
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Google GenAI Client: {e}")
        return None


def generate_gradient_fallback(colors: list, width: int = 800, height: int = 800) -> Image.Image:
    """Generates a smooth dual-color gradient image as visual fallback."""
    base = Image.new("RGB", (width, height), colors[0] if colors else "#191c16")
    top = Image.new("RGB", (width, height), colors[1] if len(colors) > 1 else "#2a45c9")

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

    accent_hex = colors[2] if len(colors) > 2 else "#b23a30"
    try:
        h = accent_hex.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        rgb = (178, 58, 48)

    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=(rgb[0], rgb[1], rgb[2], 90)
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(60))

    final_img = Image.alpha_composite(gradient_img.convert("RGBA"), overlay)
    return final_img.convert("RGB")


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

    if preferred_engine in ["Auto (Best Available)", "Gemini Imagen 3 (Default)"] and client:
        img = generate_gemini_imagen(client, prompt, aspect_ratio_str=platform)
        if img:
            return img, "Gemini Imagen 3"

    if preferred_engine in ["Auto (Best Available)", "Gemini Imagen 3 (Default)", "Pollinations AI (FLUX.1)"]:
        img = generate_pollinations_image(prompt, width=width, height=height)
        if img:
            return img, "Pollinations AI (FLUX.1)"

    if preferred_engine in ["Auto (Best Available)", "Hugging Face (FLUX)"] and hf_token:
        img = generate_hf_image(prompt, hf_token=hf_token, width=width, height=height)
        if img:
            return img, "Hugging Face (FLUX.1)"

    return generate_gradient_fallback(colors or ["#191c16", "#2a45c9", "#b23a30"], width, height), "Gradient Backdrop"


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


def _load_font(size: int, bold: bool = True):
    """Best-effort real font loading for the exported PNG (falls back to PIL default)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_composite_ad(
    bg_image: Image.Image,
    ad_data: dict,
    width: int,
    height: int,
    layout_style: str = "Modern Overlay"
) -> Image.Image:
    """Renders copy, styling overlays, and CTA button directly onto the background image using Pillow."""
    canvas = bg_image.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if layout_style == "Modern Overlay":
        for y in range(int(height * 0.35), height):
            alpha = int(220 * ((y - height * 0.35) / (height * 0.65)))
            draw.line([(0, y), (width, y)], fill=(25, 28, 22, alpha))
    elif layout_style == "Split Card":
        panel_width = int(width * 0.55)
        draw.rectangle([0, 0, panel_width, height], fill=(25, 28, 22, 230))
    else:
        draw.rectangle([0, 0, width, height], fill=(25, 28, 22, 160))

    canvas = Image.alpha_composite(canvas, overlay)
    draw_final = ImageDraw.Draw(canvas)

    headline = ad_data.get("headline", "")
    subheadline = ad_data.get("subheadline", "")
    cta = ad_data.get("cta", "SHOP NOW")

    accent_hex = ad_data.get("color_palette", {}).get("accent", "#b23a30")
    try:
        h = accent_hex.lstrip('#')
        accent_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent_rgb = (178, 58, 48)

    font_head = _load_font(int(height * 0.06), bold=True)
    font_sub = _load_font(int(height * 0.03), bold=False)
    font_badge = _load_font(int(height * 0.024), bold=True)

    # Badge
    draw_final.rectangle([40, 40, 210, 78], fill=(*accent_rgb, 210))
    draw_final.text((55, 50), "SPONSORED", fill=(255, 255, 255), font=font_badge)

    if layout_style == "Split Card":
        text_x = 40
        max_width = int(width * 0.5)
        start_y = int(height * 0.25)
    else:
        text_x = 40
        max_width = width - 80
        start_y = int(height * 0.55)

    def wrap_text(text, font, max_w):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw_final.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    y = start_y
    for line in wrap_text(headline.upper(), font_head, max_width):
        draw_final.text((text_x, y), line, fill=(255, 255, 255), font=font_head)
        y += int(height * 0.075)

    y += int(height * 0.01)
    for line in wrap_text(subheadline, font_sub, max_width):
        draw_final.text((text_x, y), line, fill=(220, 222, 210), font=font_sub)
        y += int(height * 0.04)

    btn_y = y + int(height * 0.02)
    cta_text = cta.upper()
    cta_w = int(draw_final.textlength(cta_text, font=font_sub)) + 50
    draw_final.rectangle([text_x, btn_y, text_x + cta_w, btn_y + 52], fill=(*accent_rgb, 255))
    draw_final.text((text_x + 25, btn_y + 15), cta_text, fill=(255, 255, 255), font=font_sub)

    return canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Inbuilt canvas editor ("Retouch") — Fabric.js, entirely client-side.
# Drag, resize and restyle every element, then export straight from the
# browser as a flattened PNG. No round trip through Streamlit needed.
# ---------------------------------------------------------------------------
EDITOR_TEMPLATE = r"""
<link href="https://fonts.googleapis.com/css2?family=__HEADER_FONT_URL__:wght@700;800&family=__BODY_FONT_URL__:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.0/fabric.min.js"></script>
<style>
  .retouch-wrap { font-family: 'IBM Plex Sans', sans-serif; }
  .retouch-toolbar {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    padding: 10px 12px; background: #e2e3da; border: 1px solid #191c16; border-bottom: none;
  }
  .retouch-toolbar button {
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;
    background: #f7f6f0; border: 1px solid #191c16; padding: 7px 10px; cursor: pointer; color: #191c16;
  }
  .retouch-toolbar button:hover { background: #191c16; color: #f7f6f0; }
  .retouch-toolbar button.danger:hover { background: #b23a30; border-color: #b23a30; }
  .retouch-toolbar label { font-family: 'IBM Plex Mono', monospace; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #565a4f; display: flex; align-items: center; gap: 4px; }
  .retouch-toolbar input[type=color] { width: 28px; height: 26px; border: 1px solid #191c16; padding: 0; cursor: pointer; }
  .retouch-toolbar input[type=number] { width: 52px; border: 1px solid #191c16; padding: 4px; font-family: 'IBM Plex Mono', monospace; }
  #retouchCanvasHost { border: 1px solid #191c16; background: #444; }
  .retouch-hint { font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; color: #565a4f; padding: 8px 12px; letter-spacing: 0.02em; }
</style>

<div class="retouch-wrap">
  <div class="retouch-toolbar">
    <button id="btnAddText">+ Text</button>
    <button id="btnAddRect">+ Shape</button>
    <label>Fill <input type="color" id="colorPicker" value="#ffffff"></label>
    <label>Size <input type="number" id="sizeInput" value="32" min="8" max="140"></label>
    <button id="btnFront">Bring Front</button>
    <button id="btnBack">Send Back</button>
    <button id="btnDelete" class="danger">Delete</button>
    <button id="btnDownload" style="margin-left:auto; background:#b23a30; color:#fdf9f2;">⬇ Export PNG</button>
  </div>
  <canvas id="retouchCanvasHost" width="__WIDTH__" height="__HEIGHT__"></canvas>
  <div class="retouch-hint">Drag to move &middot; corner handles to resize/rotate &middot; double‑click text to edit copy directly on the proof.</div>
</div>

<script>
(function() {
  const canvas = new fabric.Canvas('retouchCanvasHost', { preserveObjectStacking: true });

  fabric.Image.fromURL('data:image/png;base64,__BG_B64__', function(img) {
    img.scaleToWidth(__WIDTH__);
    canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas));
  }, { crossOrigin: 'anonymous' });

  const scrim = new fabric.Rect({
    left: 0, top: __HEIGHT__ * 0.42, width: __WIDTH__, height: __HEIGHT__ * 0.58,
    fill: 'rgba(15,15,12,0.52)', selectable: true, hasRotatingPoint: false
  });
  canvas.add(scrim);

  const badge = new fabric.Rect({ left: 36, top: 36, width: 150, height: 34, fill: '__ACCENT__' });
  const badgeText = new fabric.Textbox('SPONSORED', {
    left: 50, top: 44, fontSize: 13, fontFamily: "'IBM Plex Mono', monospace",
    fontWeight: '600', fill: '#ffffff', width: 130
  });
  canvas.add(badge, badgeText);

  const headline = new fabric.Textbox(__HEADLINE_JSON__, {
    left: 40, top: __HEIGHT__ * 0.52, width: __WIDTH__ - 80,
    fontSize: __HEAD_SIZE__, fontWeight: '800', fill: '__TEXT_COLOR__',
    fontFamily: "'__HEADER_FONT__', sans-serif", lineHeight: 1.05
  });
  canvas.add(headline);

  const subheadline = new fabric.Textbox(__SUBHEADLINE_JSON__, {
    left: 40, top: __HEIGHT__ * 0.68, width: __WIDTH__ - 100,
    fontSize: __SUB_SIZE__, fill: '#e5e6dc',
    fontFamily: "'__BODY_FONT__', sans-serif", lineHeight: 1.3
  });
  canvas.add(subheadline);

  const ctaRect = new fabric.Rect({
    left: 40, top: __HEIGHT__ * 0.85, width: 220, height: 50, fill: '__ACCENT__'
  });
  const ctaText = new fabric.Textbox(__CTA_JSON__, {
    left: 62, top: __HEIGHT__ * 0.85 + 16, fontSize: 15, fontWeight: '700',
    fill: '#ffffff', fontFamily: "'IBM Plex Mono', monospace", width: 190
  });
  canvas.add(ctaRect, ctaText);

  canvas.renderAll();

  function activeIsText(o) { return o && (o.type === 'textbox' || o.type === 'text'); }

  document.getElementById('btnAddText').onclick = function() {
    const t = new fabric.Textbox('New line of copy', {
      left: 60, top: 60, fontSize: 28, fill: '#ffffff',
      fontFamily: "'__BODY_FONT__', sans-serif", width: 300
    });
    canvas.add(t); canvas.setActiveObject(t);
  };

  document.getElementById('btnAddRect').onclick = function() {
    const r = new fabric.Rect({ left: 80, top: 80, width: 160, height: 60, fill: '__ACCENT__' });
    canvas.add(r); canvas.setActiveObject(r);
  };

  document.getElementById('colorPicker').oninput = function(e) {
    const o = canvas.getActiveObject();
    if (o) { o.set('fill', e.target.value); canvas.renderAll(); }
  };

  document.getElementById('sizeInput').onchange = function(e) {
    const o = canvas.getActiveObject();
    if (o && activeIsText(o)) { o.set('fontSize', parseInt(e.target.value, 10)); canvas.renderAll(); }
  };

  document.getElementById('btnFront').onclick = function() {
    const o = canvas.getActiveObject(); if (o) canvas.bringToFront(o);
  };
  document.getElementById('btnBack').onclick = function() {
    const o = canvas.getActiveObject(); if (o) canvas.sendToBack(o);
  };
  document.getElementById('btnDelete').onclick = function() {
    const o = canvas.getActiveObject(); if (o) canvas.remove(o);
  };

  document.getElementById('btnDownload').onclick = function() {
    canvas.discardActiveObject(); canvas.renderAll();
    const dataURL = canvas.toDataURL({ format: 'png', multiplier: 2 });
    const link = document.createElement('a');
    link.download = '__FILE_NAME__';
    link.href = dataURL;
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
  };
})();
</script>
"""


def render_canvas_editor(bg_image: Image.Image, ad: dict, palette: dict, fonts: dict,
                          width: int, height: int, file_name: str) -> str:
    buffered = io.BytesIO()
    bg_image.resize((width, height), Image.Resampling.LANCZOS).save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    header_font = fonts.get("header", "Big Shoulders Display") or "Big Shoulders Display"
    body_font = fonts.get("body", "IBM Plex Sans") or "IBM Plex Sans"
    accent = palette.get("accent", "#b23a30")
    text_color = palette.get("text", "#ffffff")

    head_size = max(24, int(height * 0.075))
    sub_size = max(14, int(height * 0.032))

    html = EDITOR_TEMPLATE
    html = html.replace("__WIDTH__", str(width))
    html = html.replace("__HEIGHT__", str(height))
    html = html.replace("__BG_B64__", img_b64)
    html = html.replace("__ACCENT__", accent)
    html = html.replace("__TEXT_COLOR__", text_color)
    html = html.replace("__HEADER_FONT__", header_font)
    html = html.replace("__BODY_FONT__", body_font)
    html = html.replace("__HEADER_FONT_URL__", header_font.replace(" ", "+"))
    html = html.replace("__BODY_FONT_URL__", body_font.replace(" ", "+"))
    html = html.replace("__HEAD_SIZE__", str(head_size))
    html = html.replace("__SUB_SIZE__", str(sub_size))
    html = html.replace("__HEADLINE_JSON__", json.dumps(ad.get("headline", "")))
    html = html.replace("__SUBHEADLINE_JSON__", json.dumps(ad.get("subheadline", "")))
    html = html.replace("__CTA_JSON__", json.dumps(ad.get("cta", "Shop Now")))
    html = html.replace("__FILE_NAME__", file_name)
    return html


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
DIMS = {
    "Instagram Post (1:1 Square)": (800, 800),
    "Facebook / LinkedIn Feed (1.91:1 Banner)": (955, 500),
    "Twitter / X Header (3:1 Landscape)": (900, 300),
    "Story / Mobile Vertical (9:16)": (540, 960),
    "Web Display Banner (16:9)": (960, 540)
}


def main():
    st.markdown(f"""
    <div class="ticket-strip">
        <div>
            <div class="wordmark">ADGEN<span>.</span></div>
            <span class="wordmark-sub">AI ad studio — copy, palette &amp; visual in one pass</span>
        </div>
        <div class="ticket-right">SESSION <b>№ {st.session_state.job_number}</b><br>{dt.date.today().strftime('%d %b %Y')}</div>
    </div>
    <div class="ticket-rule"></div>
    """, unsafe_allow_html=True)

    # ---- Sidebar: connections + engine + running spec, not the brief itself ----
    with st.sidebar:
        env_gemini = os.getenv("GEMINI_API_KEY", "")
        if not env_gemini:
            try:
                if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                    env_gemini = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass

        env_hf = os.getenv("HF_TOKEN", "") or os.getenv("HF_API_KEY", "")
        if not env_hf:
            try:
                if hasattr(st, "secrets") and "HF_TOKEN" in st.secrets:
                    env_hf = st.secrets["HF_TOKEN"]
            except Exception:
                pass

        st.markdown("**Connections**")
        with st.expander("API credentials", expanded=not bool(env_gemini)):
            user_gemini_key = st.text_input(
                "Gemini API Key", type="password",
                placeholder="Enter API key..." if not env_gemini else "🔒 Using server key (Enter to override)",
                help="Free key from https://aistudio.google.com/app/apikey"
            )
            gemini_api_key = user_gemini_key if user_gemini_key.strip() else env_gemini
            if env_gemini and not user_gemini_key:
                st.caption("🔒 Gemini key active from environment")

            user_hf_token = st.text_input(
                "Hugging Face Token (optional)", type="password",
                placeholder="Enter HF token..." if not env_hf else "🔒 Using server token (Enter to override)",
                help="Free token from https://huggingface.co/settings/tokens (for FLUX.1)"
            )
            hf_token = user_hf_token if user_hf_token.strip() else env_hf
            if env_hf and not user_hf_token:
                st.caption("🔒 HF token active from environment")

        st.divider()
        st.markdown("**Image engine**")
        preferred_engine = st.selectbox(
            "Engine", ["Gemini Imagen 3 (Default)", "Pollinations AI (FLUX.1)",
                       "Hugging Face (FLUX)", "Auto (Best Available)"],
            label_visibility="collapsed"
        )

        st.divider()
        if st.session_state.get("ad_package"):
            ad_sb = st.session_state.ad_package
            st.markdown("**Running spec**")
            st.caption(f"Emotion: {ad_sb.get('target_emotion','—')}")
            st.caption(f"Source: {st.session_state.get('img_source','—')}")

    if not gemini_api_key:
        st.warning("Add a **Gemini API key** under Connections in the sidebar to open the desk.")
        st.markdown("""
        1. Grab a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).
        2. Paste it in the sidebar, or set `GEMINI_API_KEY` in your `.env` file.
        3. Gemini Imagen 3 handles the product visual by default — Pollinations and Hugging Face are drop-in alternates.
        """)
        return

    for key, default in [("ad_package", None), ("bg_image", None), ("img_source", None)]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ---- The brief lives in the main column, not buried in the sidebar ----
    st.markdown('<div class="brief-eyebrow">01 — Creative Brief <span style="color:#70788b;font-size:.6rem;letter-spacing:.08em;">BUILD YOUR CAMPAIGN</span></div>', unsafe_allow_html=True)

    with st.form("brief_form"):
        col_a, col_b = st.columns([1.3, 1])
        with col_a:
            product_name = st.text_input("Product / service name", value="LuminoSound Pro")
            product_desc = st.text_area(
                "Description & key features",
                value="Wireless noise-canceling headphones with 40-hour battery life, spatial audio, "
                      "hyper-comfortable memory foam earcups, and sleek matte finish.",
                height=100
            )
            cta_focus = st.selectbox(
                "Call-to-action goal",
                ["Direct Sale (e.g. 'Shop Now - 20% Off')", "Free Trial / Signup",
                 "Lead Generation / Learn More", "Limited Time Urgency"]
            )
        with col_b:
            audience_preset = st.selectbox(
                "Target audience",
                ["Tech Enthusiasts & Creators", "Students & Young Professionals", "Fitness & Athletes",
                 "Corporate Executives", "Gamers & Streamers", "Custom / Other"]
            )
            audience_custom = st.text_input("Custom audience (used if 'Custom / Other' above)",
                                             value="Remote workers & digital nomads")
            platform = st.selectbox("Ad format / platform", list(DIMS.keys()))
            brand_tone = st.selectbox(
                "Brand style / tone",
                ["Futuristic & Cyberpunk", "Minimalist & Clean", "Bold & Energetic",
                 "Luxury & Premium", "Professional & Authoritative", "Fun & Playful"]
            )
        generate_btn = st.form_submit_button("Run the proof →", type="primary", use_container_width=True)

    target_audience = audience_custom if audience_preset == "Custom / Other" else audience_preset

    if generate_btn:
        with st.spinner("Drafting copy, palette and image brief with Gemini…"):
            client = get_gemini_client(gemini_api_key)
            if not client:
                return
            try:
                ad_data = generate_ad_campaign(
                    client, product_name, product_desc, target_audience, platform, brand_tone, cta_focus
                )
                st.session_state.ad_package = ad_data
            except Exception as e:
                st.error(f"Failed to generate ad campaign with Gemini: {e}")
                return

        w, h = DIMS.get(platform, (800, 800))
        colors = [
            st.session_state.ad_package.get("color_palette", {}).get("primary", "#191c16"),
            st.session_state.ad_package.get("color_palette", {}).get("secondary", "#2a45c9"),
            st.session_state.ad_package.get("color_palette", {}).get("accent", "#b23a30")
        ]

        with st.spinner(f"Rendering product visual via {preferred_engine}…"):
            img_prompt = st.session_state.ad_package.get("background_image_prompt", product_name)
            img, source = generate_ad_image(
                prompt=img_prompt, client=client, hf_token=hf_token,
                width=w, height=h, colors=colors, platform=platform,
                preferred_engine=preferred_engine
            )
            st.session_state.bg_image = img
            st.session_state.img_source = source
            st.toast(f"Proof ready — visual via {source}", icon="🖨️")

    if not (st.session_state.ad_package and st.session_state.bg_image):
        return

    ad = st.session_state.ad_package
    bg_img = st.session_state.bg_image
    palette = ad.get("color_palette", {})
    color_names = ad.get("color_names", {})
    fonts = ad.get("font_pairing", {})
    w, h = DIMS.get(platform, (800, 800))

    st.markdown('<div class="brief-eyebrow" style="margin-top:1.6rem;">02 — Proof Sheet <span style="color:#70788b;font-size:.6rem;letter-spacing:.08em;">REVIEW · REFINE · RELEASE</span></div>', unsafe_allow_html=True)

    tab_proof, tab_copy, tab_spec, tab_retouch, tab_release = st.tabs(
        ["🖼 Proof", "✍ Copy Deck", "🎛 Spec Sheet", "🖌 Retouch", "📦 Release"]
    )

    # -------------------- TAB: PROOF --------------------
    with tab_proof:
        col_preview, col_controls = st.columns([2, 1])

        with col_controls:
            st.markdown("**Layout & source**")
            st.caption(f"Visual source: {st.session_state.get('img_source', 'AI Engine')}")
            layout_style = st.radio("Overlay layout", ["Modern Overlay", "Split Card", "Full Tint Canvas"])
            st.session_state["layout_style"] = layout_style
            badge_text = st.text_input("Badge / tagline", value="NEW ARRIVAL")

            colors = [palette.get("primary", "#191c16"), palette.get("secondary", "#2a45c9"),
                      palette.get("accent", "#b23a30")]

            if st.button("↻ Regenerate visual only", use_container_width=True):
                with st.spinner("Rendering a fresh product visual…"):
                    client = get_gemini_client(gemini_api_key)
                    img_prompt = ad.get("background_image_prompt", product_name)
                    new_img, new_src = generate_ad_image(
                        prompt=img_prompt, client=client, hf_token=hf_token,
                        width=w, height=h, colors=colors, platform=platform,
                        preferred_engine=preferred_engine
                    )
                    st.session_state.bg_image = new_img
                    st.session_state.img_source = new_src
                    st.rerun()

            st.caption(f"Audience — {target_audience}")
            st.caption(f"Emotional hook — {ad.get('target_emotion', 'High value')}")

        with col_preview:
            buffered = io.BytesIO()
            bg_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            primary_color = palette.get("primary", "#191c16")
            accent_color = palette.get("accent", "#b23a30")
            text_color = palette.get("text", "#ffffff")
            header_font = fonts.get("header", "Big Shoulders Display")
            body_font = fonts.get("body", "IBM Plex Sans")

            gradient = ('linear-gradient(to right, rgba(15,15,12,0.94) 0%, rgba(15,15,12,0.55) 62%, rgba(0,0,0,0) 100%)'
                        if layout_style == 'Split Card' else
                        'linear-gradient(to top, rgba(15,15,12,0.95) 0%, rgba(15,15,12,0.35) 55%, rgba(0,0,0,0.05) 100%)')

            html_code = f"""
            <link href="https://fonts.googleapis.com/css2?family={header_font.replace(' ', '+')}:wght@700;800&family={body_font.replace(' ', '+')}:wght@400;600&display=swap" rel="stylesheet">
            <div class="ad-card-wrapper" style="
                background-image: url('data:image/png;base64,{img_str}');
                background-size: cover; background-position: center;
                min-height: 480px; display: flex; flex-direction: column; justify-content: flex-end;
                position: relative; font-family: '{body_font}', sans-serif;">
                <div class="proof-stamp">{st.session_state.get('img_source','AI ENGINE')}</div>
                <div style="position:absolute; top:0; left:0; right:0; bottom:0; background:{gradient}; z-index:1;"></div>
                <div style="position: relative; z-index: 2; padding: 2.4rem; max-width: {'58%' if layout_style == 'Split Card' else '100%'};">
                    <span style="background:{accent_color}; color:#fff; font-family:'IBM Plex Mono', monospace; font-size:0.7rem;
                        font-weight:700; letter-spacing:1.5px; padding:5px 12px; text-transform:uppercase; display:inline-block; margin-bottom:1rem;">
                        {badge_text}
                    </span>
                    <h1 style="font-family:'{header_font}', sans-serif; color:{text_color}; font-size:2.3rem; font-weight:800;
                        line-height:1.1; margin:0 0 0.7rem 0; text-shadow:0 2px 10px rgba(0,0,0,0.5);">
                        {ad.get('headline', '')}
                    </h1>
                    <p style="color:#e2e3da; font-size:1.02rem; line-height:1.5; margin:0 0 1.4rem 0; text-shadow:0 1px 5px rgba(0,0,0,0.5);">
                        {ad.get('subheadline', '')}
                    </p>
                    <div style="display:inline-block; background:{accent_color}; color:#fff; font-family:'IBM Plex Mono', monospace;
                        font-weight:700; font-size:0.85rem; letter-spacing:0.05em; padding:13px 26px; text-transform:uppercase;">
                        {ad.get('cta', 'Shop Now')} →
                    </div>
                </div>
            </div>
            """
            st.components.v1.html(html_code, height=520, scrolling=False)

    # -------------------- TAB: COPY DECK --------------------
    with tab_copy:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Primary headline**")
            st.code(ad.get("headline", ""), language="text")
            st.markdown("**Subheadline / body copy**")
            st.code(ad.get("subheadline", ""), language="text")
            st.markdown("**Call to action**")
            st.code(ad.get("cta", ""), language="text")
        with c2:
            st.markdown("**Strategy angle**")
            st.info(ad.get("copywriting_angle", "Targeted psychological hook."))
            st.markdown("**Image brief sent to the engine**")
            st.code(ad.get("background_image_prompt", ""), language="text")

    # -------------------- TAB: SPEC SHEET --------------------
    with tab_spec:
        st.markdown("**Color palette**")
        palette_html = ""
        for key in ["primary", "secondary", "accent", "background", "text"]:
            hex_val = palette.get(key, "#ffffff")
            c_name = color_names.get(key, key.capitalize())
            palette_html += f"""
            <div class="color-chip">
                <div class="swatch-circle" style="background-color: {hex_val};"></div>
                <span><b>{key.capitalize()}</b> — {hex_val} ({c_name})</span>
            </div>
            """
        st.markdown(f"<div>{palette_html}</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown("**Typography**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"Header — `{fonts.get('header', 'Big Shoulders Display')}`")
            st.caption("Headlines, badges, high-impact text.")
        with col_f2:
            st.markdown(f"Body — `{fonts.get('body', 'IBM Plex Sans')}`")
            st.caption("Body copy and mobile legibility.")

    # -------------------- TAB: RETOUCH (inbuilt canvas editor) --------------------
    with tab_retouch:
        st.markdown("**Inbuilt editor** — drag, resize, retype and recolor every element, then export straight "
                     "from the browser. Nothing here round-trips through the server.")
        file_name = f"{product_name.lower().replace(' ', '_') or 'ad'}_retouched.png"
        editor_html = render_canvas_editor(bg_img, ad, palette, fonts, w, h, file_name)
        st.components.v1.html(editor_html, height=h + 130, scrolling=True)

    # -------------------- TAB: RELEASE (export) --------------------
    with tab_release:
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            st.markdown("**Download flattened PNG**")
            st.write("A single composite image with text, scrim and CTA baked in — the server-rendered version.")
            composite_img = create_composite_ad(bg_img, ad, width=800, height=800,
                                                 layout_style=st.session_state.get("layout_style", "Modern Overlay"))
            buf = io.BytesIO()
            composite_img.save(buf, format="PNG")
            st.download_button(
                "⬇ Download proof PNG", data=buf.getvalue(),
                file_name=f"{product_name.lower().replace(' ', '_')}_ad.png",
                mime="image/png", use_container_width=True, type="primary"
            )
            st.caption("Prefer your hand-edited version? Use Export PNG on the Retouch tab instead.")

        with col_exp2:
            st.markdown("**Continue in Canva**")
            st.write("Open Canva pre-searched for templates matching this creative direction.")
            canva_keywords = "+".join(ad.get("canva_template_keywords", [product_name, brand_tone, "ad"]))
            canva_url = f"https://www.canva.com/search?q={canva_keywords}+ad+template"
            st.markdown(f'<a href="{canva_url}" target="_blank" class="canva-btn">Open in Canva ↗</a>',
                        unsafe_allow_html=True)

        st.divider()
        st.markdown("**Campaign JSON payload**")
        st.json(ad)


if __name__ == "__main__":
    main()