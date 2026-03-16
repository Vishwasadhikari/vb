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


class AuthSignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")


class AuthLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class AuthTokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")


class MeResponse(BaseModel):
    email: str


class ProfileResponse(BaseModel):
    email: str
    name: str | None = None
    handle: str | None = None
    bio: str | None = None


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    handle: str | None = None
    bio: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
