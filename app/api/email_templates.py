from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.models import User, UserEmailTemplate
from app.schemas.email_template import EmailTemplateCreate, EmailTemplateResponse


router = APIRouter()

@router.post("/",response_model=EmailTemplateResponse,status_code=status.HTTP_201_CREATED)
async def create_email_template(
    payload : EmailTemplateCreate,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """
    Create a new email template for the current user. If is_default = True,
    unmarks any previously-default template so onlu one stays default.
    """

    if payload.is_default:
        result = await db.execute(
            select(UserEmailTemplate).where(
                UserEmailTemplate.user_id == current_user.id,
                UserEmailTemplate.is_default == True
            )
        ) 

        for existing_default in result.scalars().all():
            existing_default.is_default = False 

    template = UserEmailTemplate(
        user_id = current_user.id,
        name = payload.name,
        subject = payload.subject,
        content = payload.content,
        is_default = payload.is_default,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template) # what is this commad does 

    return template


@router.get("/",response_model = List[EmailTemplateResponse])
async def list_email_templates(
    curret_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """
    List all email templates belongig to the current user.
    """
    result = await db.execute(select(UserEmailTemplate).where(UserEmailTemplate.user_id == curret_user.id))

    return result.scalars().all()


@router.post("/{template_id}/set-default", response_model = EmailTemplateResponse)
async def set_default_template(
    template_id : int , 
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    Marks the given template (must belong to the current user) as the
    default, unmarking any other template that was previously default
    """
    result = await db.execute(
        select(UserEmailTemplate).where(
            UserEmailTemplate.id == template_id , 
            UserEmailTemplate.user_id == current_user.id,
        )
    )

    template = result.scalar_one_or_none()

    if template is None :
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Template not found"
        )

    result = await db.execute(
            select(UserEmailTemplate).where(
                UserEmailTemplate.user_id == current_user.id,
                UserEmailTemplate.is_default == True                        
        )   
    )  # this will return multiple template right in database we are settin the default to false  then why in below line we are setting is_default false 

    for existing_default in result.scalars().all():
        existing_default.is_default = False
        
        
    template.is_default = True 
    await db.commit()
    await db.refresh(template)

    return template     



    