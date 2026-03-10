from pydantic import BaseModel, Field


class GenerateScriptRequest(BaseModel):
    prompt: str = Field(..., description="High-level description of the Roblox game or change")
    image_data: str | None = Field(
        default=None,
        description="Optional image as a data URL (e.g. data:image/png;base64,...) to guide generation",
    )
    image_data_list: list[str] | None = Field(
        default=None,
        description="Optional list of up to 2 images as data URLs (data:image/...;base64,...) to guide generation",
    )
    style: str | None = Field(
        default=None,
        description="Optional style or genre, e.g. 'obby', 'simulator', 'tycoon'",
    )
    max_tokens: int | None = Field(
        default=800,
        description="Upper bound on generated Lua tokens (model-dependent)",
        ge=100,
        le=4000,
    )


class GeneratedScript(BaseModel):
    lua_code: str = Field(..., description="Roblox Lua script ready to paste into Studio")
    description: str = Field(..., description="Plain-language summary of what the code does")
    setup_steps: list[str] | None = Field(
        default=None,
        description="Optional short steps for setting up this script in Roblox Studio",
    )


class GenerateScriptResponse(BaseModel):
    script: GeneratedScript
