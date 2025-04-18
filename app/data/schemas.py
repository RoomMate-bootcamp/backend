from pydantic import BaseModel

# example
class LoginRequest(BaseModel):
    username: str
    password: str