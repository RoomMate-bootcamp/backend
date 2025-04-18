from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ProfileBase(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    occupation: str | None = None
    avatar: str | None = None
    bio: str | None = None
    interests: list[str] | None = None
    cleanliness_level: int | None = Field(None, ge=1, le=5)
    sleep_habits: str | None = None
    rent_budget: int | None = None
    location: str | None = None
    smoking_preference: str | None = None
    pet_preference: str | None = None


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class RoommateResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
