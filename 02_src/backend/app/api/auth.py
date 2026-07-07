import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends, Header, status
from app.memory.manager import supabase_memory
from app.models.schemas import UserSignup, UserLogin, AuthResponse, UserProfile
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Dependency: Get Current User ──────────────────────────────
async def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Verifies the Supabase JWT token and returns the corresponding database user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    if not supabase_memory.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )

    try:
        # Let Supabase Auth verify the JWT
        res = await supabase_memory.client.auth.get_user(token)
        if not res or not res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Look up user in public.users table by auth_user_id
        db_user = await supabase_memory.get_user_by_auth_id(res.user.id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found in database"
            )
        return db_user
    except Exception as e:
        logger.warning(f"Auth verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

# ── Auth Endpoints ───────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(payload: UserSignup):
    """
    Creates a new Supabase Auth user, runs security checks on the guest account,
    and links the guest profile history to the new user.
    """
    if not supabase_memory.client:
        raise HTTPException(503, "Database service not available")

    # 1. Security Checks on guest_user_id
    guest_user = await supabase_memory.get_user(payload.guest_user_id)
    if not guest_user:
        # Guest never uploaded a CV so their row doesn't exist yet — create it now
        guest_user = await supabase_memory.upsert_user(
            user_id=payload.guest_user_id,
            email="",
            name="",
            is_guest=True
        )
    if not guest_user.get("is_guest", True):
        raise HTTPException(400, "Account already claimed")
    if guest_user.get("auth_user_id"):
        raise HTTPException(400, "Account already linked to another auth user")

    try:
        # 2. Create user in Supabase Auth (using admin client to auto-confirm email)
        auth_res = await supabase_memory.client.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {"name": payload.name}
        })
        
        if not auth_res or not auth_res.user:
            raise HTTPException(400, "Failed to create authentication account")
        
        auth_id = auth_res.user.id

        # 3. Claim account: link auth_user_id and set is_guest = False
        db_user = await supabase_memory.claim_account(
            guest_id=payload.guest_user_id,
            auth_id=auth_id,
            email=payload.email,
            name=payload.name
        )

        # 4. Sign in statelessly using REST API to generate a session/JWT
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={"apikey": settings.SUPABASE_ANON_KEY},
                json={"email": payload.email, "password": payload.password}
            )
            if res.status_code != 200:
                raise HTTPException(500, "User registered but login token generation failed")
            data = res.json()
            access_token = data.get("access_token")

        return AuthResponse(
            access_token=access_token,
            user=UserProfile(
                user_id=db_user["user_id"], # Keep the original guest UUID as the primary API key/ID
                email=db_user.get("email") or "",
                name=db_user.get("name") or "",
                created_at=db_user.get("created_at"),
                latest_analysis_id=db_user.get("latest_analysis_id")
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Signup failed: {e}")
        # Clean up auth user if DB mapping failed
        try:
            if 'auth_id' in locals():
                await supabase_memory.client.auth.admin.delete_user(auth_id)
        except Exception:
            pass
        raise HTTPException(400, f"Registration failed: {str(e)}")


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLogin):
    """
    Authenticates a user and returns a token along with their linked profile.
    """
    if not supabase_memory.client:
        raise HTTPException(503, "Database service not available")

    try:
        # 1. Authenticate with Supabase statelessly
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={"apikey": settings.SUPABASE_ANON_KEY},
                json={"email": payload.email, "password": payload.password}
            )
            if res.status_code != 200:
                raise HTTPException(401, "Invalid email or password")
            data = res.json()
            access_token = data.get("access_token")
            auth_id = data.get("user", {}).get("id")
            user_email = data.get("user", {}).get("email") or payload.email
            user_name = data.get("user", {}).get("user_metadata", {}).get("name", "")

        # 2. Retrieve the public profile matching the auth_id
        db_user = await supabase_memory.get_user_by_auth_id(auth_id)
        if not db_user:
            # If they exist in auth but not in our users table, create a profile row for them
            db_user = await supabase_memory.upsert_user(
                user_id=auth_id, # Fallback to using their auth_id if they didn't have a guest_id
                email=user_email,
                name=user_name,
                is_guest=False
            )
            # Link it
            await supabase_memory.client.table("users").update({"auth_user_id": auth_id}).eq("user_id", db_user["user_id"]).execute()

        return AuthResponse(
            access_token=access_token,
            user=UserProfile(
                user_id=db_user["user_id"],
                # Prefer the name from our DB; fall back to Supabase auth metadata
                email=db_user.get("email") or user_email,
                name=db_user.get("name") or user_name or "",
                created_at=db_user.get("created_at"),
                latest_analysis_id=db_user.get("latest_analysis_id")
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(401, f"Authentication failed: {str(e)}")
