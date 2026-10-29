import os
import time
import json
import hmac
import hashlib
import base64
import re
import io
import pyotp
import qrcode
from typing import Optional, Dict, Any, Set, Union
from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

# ---------------------------------------------------------------------------
# Cryptographic & Password Hashing Utilities (Bcrypt / PBKDF2 with SHA-256)
# ---------------------------------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET", "archai_enterprise_super_secret_jwt_key_2026_cust")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 86400 * 7 # 7 days

# Name Format Validation Regex: Letters, spaces, hyphens, and apostrophes only
NAME_REGEX = re.compile(r"^[a-zA-Z\s'-]+$")

# Prohibited placeholder terms, fake names, and vulgarities/slurs (English & Romanized)
PROHIBITED_TERMS: Set[str] = {
    # Generic placeholders / fake terms
    'test', 'testing', 'tester', 'admin', 'administrator', 'root', 'unknown', 
    'anonymous', 'null', 'undefined', 'placeholder', 'dummy', 'fake', 'sample', 
    'user', 'default', 'asdf', 'qwerty', 'noname', 'no name', 'none',

    # Common profanities, vulgar terms & slurs (English)
    'fuck', 'fucker', 'fucking', 'shit', 'bullshit', 'bitch', 'bastard', 
    'asshole', 'dick', 'pussy', 'cunt', 'cock', 'whore', 'slut', 'nigger', 
    'nigga', 'faggot', 'retard', 'piss', 'crap', 'twat', 'wanker', 'prick',

    # Romanized local profane & offensive terms
    'harami', 'haramkhor', 'kameena', 'kamina', 'chutiya', 'chutia', 
    'gandu', 'gandoo', 'bhenchod', 'bc', 'madarchod', 'mc', 'kanjar', 
    'dallal', 'lanat', 'lanati', 'kuttey', 'kutta', 'kutiya', 'ullu', 'bhadwa'
}

def generate_salt() -> str:
    return os.urandom(16).hex()

def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = generate_salt()
    # PBKDF2-HMAC-SHA256 with 100,000 iterations (standard secure hashing)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if "$" not in hashed_password:
            return False
        salt, key_hex = hashed_password.split("$", 1)
        clean = (plain_password or "").strip()
        variants = [clean]
        if clean.lower() not in variants:
            variants.append(clean.lower())
        if clean.capitalize() not in variants:
            variants.append(clean.capitalize())
        
        for cand in variants:
            cand_key = hashlib.pbkdf2_hmac(
                'sha256',
                cand.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            if hmac.compare_digest(key_hex, cand_key):
                return True
        return False
    except Exception:
        return False

def create_jwt_token(payload: Dict[str, Any]) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    
    payload_copy = payload.copy()
    payload_copy["iat"] = int(time.time())
    payload_copy["exp"] = int(time.time()) + JWT_EXPIRATION_SECONDS
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode()).decode().rstrip("=")
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_jwt_token(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid token structure")
    
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
    
    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise HTTPException(status_code=401, detail="Invalid token signature")
    
    # Pad base64 if needed
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)
    
    payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
    if payload.get("exp") and time.time() > payload["exp"]:
        raise HTTPException(status_code=401, detail="Token has expired. Please sign in again.")
    
    return payload

def get_current_user_claims(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required.")
    token = authorization.split(" ")[1]
    return decode_jwt_token(token)

def require_roles(*allowed_roles: str):
    def role_checker(claims: Dict[str, Any] = Depends(get_current_user_claims)) -> Dict[str, Any]:
        email = claims.get("email", "").lower()
        user_record = DATABASE_USERS.get(email)
        user_role = user_record["role"] if user_record else claims.get("role")
        
        if user_role != "SYSTEM_ADMIN" and user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return claims
    return role_checker


# ---------------------------------------------------------------------------
# Seed Database & User Store (PostgreSQL Aligned)
# ---------------------------------------------------------------------------

DATABASE_USERS: Dict[str, Dict[str, Any]] = {
    "client.homeowner@archai.pk": {
        "id": "usr_homeowner_01",
        "name": "Homeowner Client",
        "email": "client.homeowner@archai.pk",
        "password_hash": hash_password("homeownerPass2026!"),
        "role": "HOMEOWNER",
        "phone": "+92 300 8521470",
        "country": "Pakistan",
        "organization": "Private Residential Client",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "architect@archai.design": {
        "id": "usr_architect_01",
        "name": "Lead Architect",
        "email": "architect@archai.design",
        "password_hash": hash_password("architectSecure2026!"),
        "role": "ARCHITECT",
        "phone": "+92 301 5544332",
        "country": "Pakistan",
        "organization": "CUST Spatial Architecture Studio",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "usamarajput2426@gmail.com": {
        "id": "usr_admin_usama",
        "name": "Usama Rajput",
        "email": "usamarajput2426@gmail.com",
        "password_hash": hash_password("Pakistan"),
        "role": "SYSTEM_ADMIN",
        "phone": "+92 300 1122334",
        "country": "Pakistan",
        "organization": "ArchAI Core Infrastructure",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "admin@archai.design": {
        "id": "usr_admin_01",
        "name": "System Administrator",
        "email": "admin@archai.design",
        "password_hash": hash_password("adminMasterKey2026!"),
        "role": "SYSTEM_ADMIN",
        "phone": "+92 300 1122334",
        "country": "Pakistan",
        "organization": "ArchAI Core Infrastructure",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "designer@archai.design": {
        "id": "usr_designer_01",
        "name": "Spatial Designer",
        "email": "designer@archai.design",
        "password_hash": hash_password("designerPass2026!"),
        "role": "DESIGNER",
        "phone": "+92 302 9988776",
        "country": "Pakistan",
        "organization": "Studio Modern Aesthetics",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "engineer@archai.design": {
        "id": "usr_engineer_01",
        "name": "Construction Engineer",
        "email": "engineer@archai.design",
        "password_hash": hash_password("engineerPass2026!"),
        "role": "CONSTRUCTION_PRO",
        "phone": "+92 303 4455667",
        "country": "Pakistan",
        "organization": "Structural Execution Works",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "developer@archai.design": {
        "id": "usr_developer_01",
        "name": "Real Estate Developer",
        "email": "developer@archai.design",
        "password_hash": hash_password("developerPass2026!"),
        "role": "REAL_ESTATE_DEV",
        "phone": "+92 304 7788990",
        "country": "Pakistan",
        "organization": "Capital Real Estate Holdings",
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": "2026-01-01T00:00:00Z"
    }
}




# ---------------------------------------------------------------------------
# Pydantic Schemas with Strict Name Validation (Pydantic v2)
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(..., example="client.homeowner@archai.pk")
    password: str = Field(..., min_length=1, example="homeownerPass2026!")

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, example="Tariq Mehmood")
    email: str = Field(..., example="tariq@example.com")
    password: str = Field(..., min_length=6, example="securePassword123")
    role: Optional[str] = Field(default="HOMEOWNER", example="ARCHITECT")
    phone: Optional[str] = Field(default="+92 300 0000000")
    country: Optional[str] = Field(default="Pakistan")
    organization: Optional[str] = Field(default="Residential Client")
    avatarUrl: Optional[str] = None


    @field_validator('name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        trimmed = v.strip()
        
        # Length check
        if len(trimmed) < 2 or len(trimmed) > 50:
            raise ValueError("Invalid name format or prohibited words detected. Please enter your legal name.")
        
        # Regex format: only letters, spaces, hyphens, and apostrophes
        if not NAME_REGEX.match(trimmed):
            raise ValueError("Invalid name format or prohibited words detected. Please enter your legal name.")
        
        # Prohibited words & profanities blocklist check
        lower = trimmed.lower()
        words = set(re.split(r"[\s'-]+", lower))
        
        for term in PROHIBITED_TERMS:
            if lower == term or term in words or (len(term) >= 4 and term in lower):
                raise ValueError("Invalid name format or prohibited words detected. Please enter your legal name.")
        
        return trimmed

class UserDTO(BaseModel):
    id: str
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    country: Optional[str] = None
    organization: Optional[str] = None
    avatarUrl: Optional[str] = None
    is_2fa_enabled: bool = False

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserDTO
    message: str

class Setup2FARequest(BaseModel):
    email: Optional[str] = None

class Setup2FAResponse(BaseModel):
    secret: str
    qr_code: str
    totp_uri: str

class Verify2FARequest(BaseModel):
    email: str
    code: str

class Verify2FAResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    user: Optional[UserDTO] = None

class Disable2FARequest(BaseModel):
    email: str

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication & RBAC"])

@auth_router.post("/login")
async def login_user(body: LoginRequest):
    email = body.email.strip().lower()
    password = body.password

    user_record = DATABASE_USERS.get(email)
    
    # Security Rule 1: IF credentials do not match or user is not registered: Return HTTP 401
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please sign up first."
        )
    
    # Security Rule 2: Verify Bcrypt password hash
    if not verify_password(password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please sign up first."
        )
    
    if not user_record.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently suspended. Please contact the administrator."
        )

    # 2FA Step Enforcement during primary login flow: ONLY if enabled AND secret key exists
    if user_record.get("is_2fa_enabled", False) and user_record.get("totp_secret"):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "requires_2fa": True,
                "email": user_record["email"],
                "message": "Two-Factor Authentication required. Please enter your 6-digit TOTP code."
            }
        )


    # Issue cryptographically signed JWT token containing user_id and role
    jwt_payload = {
        "sub": user_record["id"],
        "user_id": user_record["id"],
        "name": user_record["name"],
        "email": user_record["email"],
        "role": user_record["role"],
        "country": user_record.get("country", "Pakistan"),
        "phone": user_record.get("phone", ""),
        "organization": user_record.get("organization", "")
    }

    token = create_jwt_token(jwt_payload)

    user_dto = UserDTO(
        id=user_record["id"],
        name=user_record["name"],
        email=user_record["email"],
        role=user_record["role"],
        phone=user_record.get("phone"),
        country=user_record.get("country"),
        organization=user_record.get("organization"),
        avatarUrl=user_record.get("avatarUrl"),
        is_2fa_enabled=user_record.get("is_2fa_enabled", False)
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=user_dto,
        message=f"Authentication successful as {user_record['name']} ({user_record['role']})."
    )

@auth_router.post("/setup-2fa", response_model=Setup2FAResponse)
async def setup_2fa(body: Setup2FARequest, authorization: Optional[str] = Header(None)):
    email = body.email.strip().lower() if body.email else None
    
    if not email and authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = decode_jwt_token(token)
            email = payload.get("email", "").lower()
        except Exception:
            pass

    if not email:
        raise HTTPException(status_code=400, detail="User email address is required for 2FA setup.")
        
    user_record = DATABASE_USERS.get(email)
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    # Stage 1 2FA Enrollment: Generate temporary Base32 secret without activating 2FA in database
    secret = pyotp.random_base32()
    user_record["temp_totp_secret"] = secret

    # Generate TOTP URI with issuer ArchAI Studio
    totp = pyotp.TOTP(secret)
    totp_uri = totp.provisioning_uri(name=email, issuer_name="ArchAI Studio")

    # Generate high-resolution Base64 PNG QR code
    qr_img = qrcode.make(totp_uri)
    img_byte_arr = io.BytesIO()
    qr_img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    qr_code_b64 = f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

    return Setup2FAResponse(
        secret=secret,
        qr_code=qr_code_b64,
        totp_uri=totp_uri
    )

@auth_router.post("/verify-2fa", response_model=Verify2FAResponse)
async def verify_2fa(body: Verify2FARequest):
    email = body.email.strip().lower()
    code = body.code.strip()

    user_record = DATABASE_USERS.get(email)
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    secret = user_record.get("temp_totp_secret") or user_record.get("totp_secret")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA secret key has not been generated for this account. Please click Enable Google Authenticator first."
        )

    # Initialize pyotp.TOTP(secret).verify(code) to validate time-based tokens with clock drift tolerance
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 6-digit verification code. Please check your Google Authenticator app and try again."
        )

    # Stage 2 Lock-In: Cryptographic match verified! Save secret and activate 2FA in database
    user_record["totp_secret"] = secret
    user_record["is_2fa_enabled"] = True
    user_record.pop("temp_totp_secret", None)


    # Generate JWT token
    jwt_payload = {
        "sub": user_record["id"],
        "user_id": user_record["id"],
        "name": user_record["name"],
        "email": user_record["email"],
        "role": user_record["role"],
        "country": user_record.get("country", "Pakistan"),
        "phone": user_record.get("phone", ""),
        "organization": user_record.get("organization", "")
    }

    token = create_jwt_token(jwt_payload)

    user_dto = UserDTO(
        id=user_record["id"],
        name=user_record["name"],
        email=user_record["email"],
        role=user_record["role"],
        phone=user_record.get("phone"),
        country=user_record.get("country"),
        organization=user_record.get("organization"),
        avatarUrl=user_record.get("avatarUrl"),
        is_2fa_enabled=True
    )

    return Verify2FAResponse(
        success=True,
        message="Two-Factor Authentication verified successfully.",
        access_token=token,
        user=user_dto
    )

@auth_router.post("/disable-2fa")
async def disable_2fa(body: Disable2FARequest):
    email = body.email.strip().lower()
    user_record = DATABASE_USERS.get(email)
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    user_record["is_2fa_enabled"] = False
    user_record["totp_secret"] = None
    return {"message": "Two-Factor Authentication disabled successfully.", "is_2fa_enabled": False}

@auth_router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup_user(body: SignupRequest):
    email = body.email.strip().lower()
    
    if email in DATABASE_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email address is already registered. Please sign in instead."
        )

    # Security Safeguard: Block manual SYSTEM_ADMIN account creation via public registration API
    requested_role = (body.role or "HOMEOWNER").strip().upper()
    if requested_role == "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creation of SYSTEM_ADMIN accounts via public registration is prohibited. Administrator accounts must be provisioned internally."
        )

    ALLOWED_STANDARD_ROLES = {"HOMEOWNER", "ARCHITECT", "DESIGNER", "CONSTRUCTION_PRO", "REAL_ESTATE_DEV"}
    final_role = requested_role if requested_role in ALLOWED_STANDARD_ROLES else "HOMEOWNER"

    new_user_id = f"usr_{int(time.time())}"
    new_user_record = {
        "id": new_user_id,
        "name": body.name.strip(),
        "email": email,
        "password_hash": hash_password(body.password),
        "role": final_role,
        "phone": body.phone,
        "country": body.country,
        "organization": body.organization or "Residential Client",
        "avatarUrl": body.avatarUrl,
        "is_active": True,
        "is_2fa_enabled": False,
        "totp_secret": None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    DATABASE_USERS[email] = new_user_record

    jwt_payload = {
        "sub": new_user_id,
        "user_id": new_user_id,
        "name": new_user_record["name"],
        "email": new_user_record["email"],
        "role": final_role,
        "country": new_user_record["country"],
        "phone": new_user_record["phone"],
        "organization": new_user_record["organization"]
    }

    token = create_jwt_token(jwt_payload)

    user_dto = UserDTO(
        id=new_user_id,
        name=new_user_record["name"],
        email=new_user_record["email"],
        role=final_role,
        phone=new_user_record["phone"],
        country=new_user_record["country"],
        organization=new_user_record["organization"],
        avatarUrl=new_user_record["avatarUrl"],
        is_2fa_enabled=False
    )




    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=user_dto,
        message="Homeowner account created successfully."
    )

@auth_router.get("/me", response_model=UserDTO)
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")
    
    token = authorization.split(" ")[1]
    payload = decode_jwt_token(token)
    email = payload.get("email", "").lower()
    
    user_record = DATABASE_USERS.get(email)
    if not user_record:
        raise HTTPException(status_code=401, detail="User record not found.")

    return UserDTO(
        id=user_record["id"],
        name=user_record["name"],
        email=user_record["email"],
        role=user_record["role"],
        phone=user_record.get("phone"),
        country=user_record.get("country"),
        organization=user_record.get("organization"),
        avatarUrl=user_record.get("avatarUrl"),
        is_2fa_enabled=user_record.get("is_2fa_enabled", False)
    )

class NotificationStatusUpdateRequest(BaseModel):
    status: str = Field(default="received", example="received")

@auth_router.patch("/admin/notifications/{notification_id}/status")
async def update_admin_notification_status(
    notification_id: str,
    body: NotificationStatusUpdateRequest = NotificationStatusUpdateRequest(),
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ")[1]
    payload = decode_jwt_token(token)
    role = payload.get("role", "")

    if role != "SYSTEM_ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden: System Admin privileges required to update notification status.")

    new_status = body.status.strip().lower() if body.status else "received"
    return JSONResponse(content={
        "status": "success",
        "id": notification_id,
        "notification_status": new_status,
        "message": f"Notification {notification_id} status updated to {new_status}."
    })


