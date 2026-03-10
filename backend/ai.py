import json
import os
import re
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
from openai import OpenAI

from .schemas import GenerateScriptRequest, GeneratedScript


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
ENV_PATH = CONFIG_DIR / ".env"
BACKEND_ENV_PATH = BASE_DIR / "backend" / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
if BACKEND_ENV_PATH.exists():
    load_dotenv(BACKEND_ENV_PATH)


_SYSTEM_PROMPT = dedent(
    """
    You are an expert Roblox game developer and Lua programmer.
    The user will describe exactly what they want. You must respond with valid JSON only.

    CRITICAL — MINIMAL CODE ONLY:
    - Implement ONLY the exact behavior the user asked for. Nothing else.
    - Do NOT add boilerplate, "getting" services, or helper functions the user did not ask for.
    - Example: If the user says "when touches apple his health increases", write ONLY:
      (1) the code that runs when the apple is touched (Touched event),
      (2) get the player who touched it and increase that player's health.
      Do NOT write a long "increaseHealth(player)" helper, GetService('Players') setup, or comments like "Get the apple" unless they are necessary for the few lines that do the job.
    - Prefer a short script: assume the script lives inside the Part (e.g. "Apple"). Use `script.Parent` for the part. Connect to Touched, get the player from the touching part, then change Humanoid.Health. No extra functions or services unless needed for that single behavior.
    - Another example: "coin that gives 10 points" → only the code that detects touch and adds 10 to Points. No respawn, no extra coins, no GUI unless asked.
    - Match the scope of the request exactly: minimal, focused code.

    LEADERSTAT NAMING (when points/score are involved):
    - Use the leaderstat name "Points" (capital P) when the user mentions points or score. Do NOT use CoinsCollected, Coins, or Score unless they ask for that exact name.

    Output a single JSON object with exactly these keys:
    - "description": A detailed, ChatGPT-style, user-facing explanation that covers THREE things:
        (A) the gameplay / feature being built (what happens in-game),
        (B) how the Lua code works (key steps, events, and objects used), and
        (C) exactly WHERE and HOW to place each script and any required instances in Roblox Studio (for example: 'Put this Script in ServerScriptService as GameManager', 'Create a Folder named Zombies in Workspace and place 5 NPC models inside it').
      IMPORTANT: "description" must be a SINGLE STRING (not an array). Format it as 8–16 short bullet lines separated by newline characters (\\n), e.g.:
        "- ...\\n- ...\\n- ..."\n
      Include at least 2–4 bullets specifically about placement/setup in Studio so a beginner knows exactly where each script and object goes.
      Keep it strictly scoped to what the user asked—do NOT invent extra mechanics.
      If you must assume something (e.g., where the Script is placed), state the assumption explicitly in one line and implement accordingly.
      If the user gave an image, mention what you used from the image in 1 line (only if relevant).
    - "lua_code": A minimal, ready-to-paste Roblox Lua script that implements ONLY the described behavior. Short and focused.
    - "setup_steps": An array of 3 to 5 short strings: specific steps for setting up this script in Roblox Studio (e.g. "Create a Part named Apple in Workspace", "Put this Script inside the Apple", "Press Play and touch the apple to test"). Steps must match what the script actually does.

    Requirements for lua_code:
    - Minimal: only the logic for the requested behavior. No long intros or unnecessary helpers.
    - At the very top of lua_code, ALWAYS include one or more comment headers of the form:
        -- Script: <Service>/<OptionalFolder>/<ScriptName>
      Example for a single script: -- Script: ServerScriptService/ZombieGame
      Example for multiple scripts in one lua_code: use multiple headers to start each section, e.g.
        -- Script: ServerScriptService/ZombieAI
        ...code...
        -- Script: ServerScriptService/SurvivalTimer
        ...code...
        -- Script: StarterGui/EndScreenGui
        ...code...
      These headers tell the user exactly where to place each Script in Roblox Studio.
    - FORMAT: Use normal line breaks and indentation. One statement per line. Do NOT output one long line.
    - Correct Lua scope. Modern Roblox Lua only (GetService, Touched, Humanoid, etc.) when needed.
    - If the script is meant to go inside a Part (e.g. apple), use script.Parent as the part and keep the script short.
    - No placeholder comments like "add your logic here"; implement the behavior fully in few lines.

    Reply with only the JSON object, no markdown, no code fences, no extra text.
    """
).strip()


def _extract_description_and_lua_code(raw: str) -> dict | None:
    """When JSON is invalid (e.g. unescaped newlines in lua_code), extract the two fields."""
    # Find "description": "..." , "lua_code": "
    desc_m = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.)*?)"\s*,\s*"lua_code"\s*:\s*"', raw, re.DOTALL)
    if not desc_m:
        return None
    description = desc_m.group(1).replace("\\n", "\n").replace('\\"', '"')
    lua_start = desc_m.end()
    # Closing quote for lua_code is the " that is followed by optional whitespace and }
    end_m = re.search(r'"\s*}\s*$', raw[lua_start:], re.DOTALL)
    if end_m:
        lua_code = raw[lua_start : lua_start + end_m.start()].replace("\\n", "\n").replace('\\"', '"')
        return {"description": description, "lua_code": lua_code}
    # Fallback: find next " not preceded by backslash (simple closing quote)
    pos = lua_start
    while pos < len(raw):
        idx = raw.find('"', pos)
        if idx == -1:
            break
        n = 0
        i = idx - 1
        while i >= 0 and raw[i] == "\\":
            n += 1
            i -= 1
        if n % 2 == 0:
            lua_code = raw[lua_start:idx].replace("\\n", "\n").replace('\\"', '"')
            return {"description": description, "lua_code": lua_code}
        pos = idx + 1
    return None


def _get_groq_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError(
            "Missing Groq key. Set GROQ_API_KEY in config/.env or backend/.env (get it from console.groq.com/keys), then restart."
        )
    return api_key.strip()


def _parse_json_from_response(text: str) -> dict:
    """Extract JSON object from model output; tolerate markdown fences."""
    raw = (text or "").strip()
    if not raw:
        raise RuntimeError("Model returned empty response.")

    try:
        out = json.loads(raw)
        if isinstance(out, dict) and "lua_code" in out:
            return out
    except json.JSONDecodeError:
        pass

    if "```" in raw:
        lines = raw.splitlines()
        start = next((i for i, L in enumerate(lines) if L.strip().startswith("```")), None)
        end = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].strip().startswith("```")), None)
        if start is not None and end is not None and end > start:
            raw = "\n".join(lines[start + 1 : end])

    try:
        out = json.loads(raw)
        if isinstance(out, dict) and "lua_code" in out:
            return out
    except json.JSONDecodeError:
        pass

    i = raw.find("{")
    j = raw.rfind("}")
    if i != -1 and j != -1 and j > i:
        try:
            out = json.loads(raw[i : j + 1])
            if isinstance(out, dict) and "lua_code" in out:
                return out
        except json.JSONDecodeError:
            pass

    # Fallback: model may return JSON with unescaped newlines/quotes in lua_code; extract by scanning.
    out = _extract_description_and_lua_code(raw)
    if out is not None:
        return out

    raise RuntimeError(f"Model did not return valid JSON. Preview: {raw[:300]}...")


async def generate_roblox_script(payload: GenerateScriptRequest) -> GeneratedScript:
    """Call the Groq API (OpenAI-compatible) to generate a Roblox Lua script."""
    api_key = _get_groq_api_key()
    base_url = os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
    text_model = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
    vision_model = os.getenv("GROQ_VISION_MODEL") or "meta-llama/llama-4-scout-17b-16e-instruct"

    client = OpenAI(api_key=api_key, base_url=base_url)

    user_content = _build_user_prompt(payload)
    max_tokens = payload.max_tokens or 2000

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    images: list[str] = []
    if payload.image_data_list:
        images = [str(x).strip() for x in payload.image_data_list if str(x).strip()]
        images = images[:2]
    elif payload.image_data and payload.image_data.strip():
        images = [payload.image_data.strip()]

    if images:
        # Vision-capable request: pass images as image_url data URIs
        content_parts = [{"type": "text", "text": user_content}]
        for img in images:
            content_parts.append({"type": "image_url", "image_url": {"url": img}})

        messages.append(
            {
                "role": "user",
                "content": content_parts,
            }
        )
        model = vision_model
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
    else:
        messages.append({"role": "user", "content": user_content})
        model = text_model
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("Groq returned an empty response.")

    parsed = _parse_json_from_response(content)
    description = parsed.get("description") or "Generated Roblox script."
    lua_code = parsed.get("lua_code") or "-- No code generated."
    lua_code = _ensure_lua_line_breaks(lua_code)
    raw_steps = parsed.get("setup_steps")
    setup_steps = None
    if isinstance(raw_steps, list) and len(raw_steps) > 0:
        setup_steps = [str(s).strip() for s in raw_steps if s]

    return GeneratedScript(description=description, lua_code=lua_code, setup_steps=setup_steps)


def _ensure_lua_line_breaks(lua_code: str) -> str:
    """If the model returned one long line, split on semicolons so the code is readable."""
    if not lua_code or not lua_code.strip():
        return lua_code
    lines = lua_code.split("\n")
    if len(lines) >= 3:
        return "\n".join(l.strip() for l in lines).strip()
    one_line = " ".join(l.strip() for l in lines).strip()
    if ";" not in one_line:
        return lua_code
    parts = one_line.split(";")
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p + ";" if not p.endswith(";") else p)
    return "\n".join(out).rstrip(";").strip()


def _build_user_prompt(payload: GenerateScriptRequest) -> str:
    base = (
        "Implement only what is described below. Do not add features or mechanics that are not asked for.\n\n"
        "Use consistent leaderstat names in every script: if the game involves points or score, use the leaderstat name 'Points'. "
        "Do not use different names (e.g. CoinsCollected, Coins, Score) unless the user explicitly asks for that exact name. "
        "This way all scripts (coins, leaderboard, UI, etc.) work together.\n\n"
        f"Game idea or change:\n{payload.prompt.strip()}"
    )
    if payload.style and payload.style.strip():
        base += f"\n\nStyle/genre (optional): {payload.style.strip()}"
    return base
