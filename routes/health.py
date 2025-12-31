from fastapi import APIRouter

router = APIRouter()

# ==========================================
# 4. HEALTH CHECK
# ==========================================
@router.get("/health")
async def health():
    return {"status": "healthy", "service": "careconnect-api"}
