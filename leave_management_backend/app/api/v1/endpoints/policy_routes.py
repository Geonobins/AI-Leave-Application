from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.api.deps import get_current_user
from app.models.company_policy import CompanyPolicy
from app.models.policy_chunk import PolicyChunk
from app.services.policy_processor import PolicyProcessor
from app.services.policy_rag_service import PolicyRAGService
from app.services.policy_embedding_service import PolicyEmbeddingService
from app.config import settings
import json
from datetime import datetime

router = APIRouter()

def get_hr_user(current_user: User = Depends(get_current_user)):
    """Verify user is HR"""
    if current_user.role != UserRole.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR can manage company policies"
        )
    return current_user


@router.post("/policies/upload", status_code=status.HTTP_201_CREATED)
async def upload_policy_document(
    file: UploadFile = File(...),
    policy_type: str = "LEAVE",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Upload and process company policy document"""
    
    # Validate file type
    allowed_types = ["pdf", "docx", "doc", "txt"]
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_types}"
        )
    
    # Read file content
    file_content = await file.read()
    
    if len(file_content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Deactivate previous policies of same type
    db.query(CompanyPolicy).filter(
        CompanyPolicy.policy_type == policy_type,
        CompanyPolicy.is_active == True
    ).update({"is_active": False})
    
    # Create policy record
    policy = CompanyPolicy(
        filename=file.filename,
        file_type=file_ext,
        uploaded_by=current_user.id,
        policy_type=policy_type,
        effective_date=datetime.utcnow(),
        embedding_status="PROCESSING"
    )
    
    try:
        # Extract text
        processor = PolicyProcessor()
        extracted_text = processor.extract_text(file_content, file_ext)
        policy.extracted_text = extracted_text
        
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        # Chunk text
        chunks = processor.chunk_text(extracted_text)
        
        # Generate embeddings
        embedding_service = PolicyEmbeddingService(settings.GROQ_API_KEY)
        
        for chunk_data in chunks:
            embedding = embedding_service.generate_embedding(chunk_data["content"])
            
            chunk = PolicyChunk(
                policy_id=policy.id,
                chunk_index=chunk_data["index"],
                content=chunk_data["content"],
                embedding=json.dumps(embedding),
                section_title=chunk_data.get("section_title")
            )
            db.add(chunk)
        
        policy.embedding_status = "COMPLETED"
        db.commit()
        
        return {
            "message": "Policy uploaded and processed successfully",
            "policy_id": policy.id,
            "chunks_created": len(chunks),
            "filename": file.filename
        }
        
    except Exception as e:
        policy.embedding_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/policies")
def get_all_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get all company policies"""
    policies = db.query(CompanyPolicy).order_by(
        CompanyPolicy.upload_date.desc()
    ).all()
    
    return [{
        "id": p.id,
        "filename": p.filename,
        "policy_type": p.policy_type,
        "upload_date": p.upload_date,
        "is_active": p.is_active,
        "embedding_status": p.embedding_status,
        "version": p.version
    } for p in policies]


@router.get("/policies/{policy_id}")
def get_policy_details(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get policy details (available to all users)"""
    policy = db.query(CompanyPolicy).filter(
        CompanyPolicy.id == policy_id,
        CompanyPolicy.is_active == True
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Get chunks count
    chunks = db.query(PolicyChunk).filter(
        PolicyChunk.policy_id == policy_id
    ).count()
    
    return {
        "id": policy.id,
        "filename": policy.filename,
        "policy_type": policy.policy_type,
        "upload_date": policy.upload_date,
        "effective_date": policy.effective_date,
        "chunks_count": chunks,
        "preview": policy.extracted_text[:500] + "..." if policy.extracted_text else None
    }


@router.delete("/policies/{policy_id}")
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Delete a policy and its chunks"""
    policy = db.query(CompanyPolicy).filter(CompanyPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Delete chunks first
    db.query(PolicyChunk).filter(PolicyChunk.policy_id == policy_id).delete()
    
    # Delete policy
    db.delete(policy)
    db.commit()
    
    return {"message": "Policy deleted successfully"}


@router.post("/policies/query")
def query_policies(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query company policies (available to all users)"""
    
    rag_service = PolicyRAGService(db, settings.GROQ_API_KEY)
    results = rag_service.retrieve_relevant_policies(query, top_k)
    
    return {
        "query": query,
        "results": results
    }


@router.post("/policies/check-compliance")
def check_leave_compliance(
    leave_request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if a leave request complies with company policy"""
    
    user_context = {
        "user_id": current_user.id,
        "role": current_user.role.value,
        "department": current_user.department,
        "position": current_user.position
    }
    
    rag_service = PolicyRAGService(db, settings.GROQ_API_KEY)
    compliance_result = rag_service.check_policy_compliance(
        leave_request=leave_request,
        user_context=user_context
    )
    
    return compliance_result


@router.put("/policies/{policy_id}/activate")
def activate_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Activate a policy (deactivates others of same type)"""
    policy = db.query(CompanyPolicy).filter(CompanyPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Deactivate all policies of same type
    db.query(CompanyPolicy).filter(
        CompanyPolicy.policy_type == policy.policy_type,
        CompanyPolicy.is_active == True
    ).update({"is_active": False})
    
    # Activate this policy
    policy.is_active = True
    db.commit()
    
    return {
        "message": "Policy activated successfully",
        "policy_id": policy.id,
        "filename": policy.filename
    }


@router.get("/policies/active/{policy_type}")
def get_active_policy(
    policy_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get currently active policy for a specific type"""
    policy = db.query(CompanyPolicy).filter(
        CompanyPolicy.policy_type == policy_type,
        CompanyPolicy.is_active == True
    ).first()
    
    if not policy:
        return {
            "message": f"No active {policy_type} policy found",
            "policy": None
        }
    
    chunks_count = db.query(PolicyChunk).filter(
        PolicyChunk.policy_id == policy.id
    ).count()
    
    return {
        "id": policy.id,
        "filename": policy.filename,
        "policy_type": policy.policy_type,
        "upload_date": policy.upload_date,
        "effective_date": policy.effective_date,
        "chunks_count": chunks_count
    }


@router.get("/policies/stats")
def get_policy_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get policy statistics (HR only)"""
    from sqlalchemy import func
    
    total_policies = db.query(func.count(CompanyPolicy.id)).scalar()
    active_policies = db.query(func.count(CompanyPolicy.id)).filter(
        CompanyPolicy.is_active == True
    ).scalar()
    
    policy_types = db.query(
        CompanyPolicy.policy_type,
        func.count(CompanyPolicy.id).label('count')
    ).group_by(CompanyPolicy.policy_type).all()
    
    total_chunks = db.query(func.count(PolicyChunk.id)).scalar()
    
    return {
        "total_policies": total_policies,
        "active_policies": active_policies,
        "policy_types": [
            {"type": pt, "count": count} for pt, count in policy_types
        ],
        "total_chunks": total_chunks
    }