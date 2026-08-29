# ⚡ AI-Assisted Digital Advertisement Generator

A modern, high-converting web application that uses Google Gemini 2.5 Flash and Hugging Face FLUX.1 to generate complete digital ad campaigns—including copy, visual prompts, color palettes, font pairings, and interactive live previews.

---

## 🌟 Key Features

1. **AI Ad Copywriter**: Generates high-converting Headlines, Subheadlines, and Call-to-Actions (CTAs) using `google-genai` and `gemini-2.5-flash`.
2. **AI Image Generation & Gradient Engine**: Integrates Hugging Face's `black-forest-labs/FLUX.1-schnell` Inference API for photorealistic product visual backdrops, with an automatic **Pillow Gradient Fallback** if API keys are missing or rate-limited.
3. **Interactive Live Ad Preview**: Live responsive layout card with platform-specific aspect ratios (Instagram 1:1, Facebook 1.91:1, Twitter 3:1, Web 16:9, Story 9:16) and multi-layout toggles.
4. **Design System Engine**: Recommends harmonious HSL/Hex color palettes and Google Font pairings.
5. **Direct Action & Export Hub**:
   - One-click **Download Composite Ad Image (PNG)** rendered with PIL.
   - Direct launch link to **Canva** editor pre-filtered with relevant design templates.
   - Copywriter script and structured JSON data export.

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Clone / Navigate to Workspace
```bash
cd /path/to/advertisment
```

### 3. Create & Activate Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or install directly: `pip install google-genai streamlit requests Pillow python-dotenv`)*

---

## 🔑 Environment Configuration

Create a `.env` file in the project root directory (or copy `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required: Free key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Free token from https://huggingface.co/settings/tokens
HF_TOKEN=your_huggingface_token_here
```

> **Note:** You can also enter API keys directly in the app's sidebar interface when running!

---

## 🏃 Running the Application

Launch the Streamlit app locally:

```bash
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
advertisment/
├── app.py              # Main Streamlit Application & AI Engine
├── requirements.txt    # Required Python packages
├── .env.example        # Environment variable template
├── .env                # Local API credentials file (ignored in git)
└── README.md           # Documentation & instructions
```

---

## 🛡️ Error Handling & Fallbacks

- **Missing Gemini API Key**: Clear notification banner instructing how to obtain a free key from Google AI Studio.
- **Missing / Rate-Limited HF Token**: If Hugging Face API is unavailable, the application automatically invokes a custom PIL radial/linear gradient engine using your generated brand color palette, guaranteeing zero crashes.
