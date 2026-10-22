from fastapi import APIRouter, Depends, HTTPException,status
from jinja2 import TemplateSyntaxError
from sqlalchemy import select, func 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.models import User, UserEmailTemplate
from app.schemas.email_template import EmailTemplateCreate, EmailTemplatePreviewRequest , EmailTemplatePreviewResponse , EmailTemplateResponse , EmailTemplateUpdate
from app.services.cold_email_service import render_cold_email


router = APIRouter()

def sample_context(user: User) -> dict : 
    """
    The same variables a real send fills in, with a made-up recruiter
    and the user's own details, so templates can be previewed and 
    checked before any email goes out.
    """
    return {
        "hr_name" : "Priya Sharma",
        "company_name": "Zoho",
        "job_position": "Backend Developer",
        "experience_years": 3,
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "applicant_name": user.name,
        "email": user.email,
        "contact_number": user.mobile or "98765 43210",
        "linkedin_url": "https://www.linkedin.com/in/your-profile",
    }


def render_or_400(subject: str | None, content: str, context: dict) -> tuple[str,str]:
    """
    Renders a template exactly like a real send (an empty subject falls 
    back to the same default subject). A mistake in the template, such
    as an unclosed {{ }}, becomes a 400 that says where it is, instead 
    of failing later when emails are sent. 
    """
    try:
        body = render_cold_email(content, context)
        if subject:
            rendered_subject = render_cold_email(subject,context)
        else:
            rendered_subject = f"{context['job_position']} | Inquiry About Openings - {context['applicant_name']}"
    except TemplateSyntaxError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template error on line {exc.lineno}: {exc.message}",
        )
    except Exception as exc :
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail=f"Template error: {exc}",
        )
    return rendered_subject,body


async def get_own_template(db: AsyncSession, user_id : int, template_id: int)-> UserEmailTemplate:
    """
    The user's own template with this id, or 404 (also for someone 
    else's template, so ids of other user's templates are not revealed).
    """
    result = await db.execute(
        select(UserEmailTemplate).where(
            UserEmailTemplate.id == template_id,
            UserEmailTemplate.user_id == user_id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Template not found")
    return template


@router.post("/",response_model=EmailTemplateResponse,status_code=status.HTTP_201_CREATED)
async def create_email_template(
    payload : EmailTemplateCreate,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """
    Create a new email template for the current user. If is_default = True,
    unmarks any previously-default template so only one stays default.
    The user's first template becomes the default even if not asked,
    since emails can't be sent without one.
    """
    render_or_400(payload.subject,payload.content, sample_context(current_user))

    has_default = await db.scalar(
        select(func.count()).select_from(UserEmailTemplate).where(
            UserEmailTemplate.user_id == current_user.id,
            UserEmailTemplate.is_default == True,
        )
    )

    make_default = payload.is_default or not has_default

    if make_default:
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
        is_default = make_default,
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


@router.post("/preview", response_model=EmailTemplatePreviewResponse)
async def preview_email_template(
    payload : EmailTemplatePreviewRequest,
    current_user : User = Depends(get_current_user)
):
    """
    Shows how a template (saved or not) reads once filled in, using a 
    sample recruiter and the user's own details. Nothing is saved or sent.
    """

    subject, body = render_or_400(payload.subject, payload.content, sample_context(current_user))
    return EmailTemplatePreviewResponse(subject=subject,body=body)


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id : int, 
    payload : EmailTemplateUpdate,
    current_user : User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Changes a template's name, subject , and content. Which template is 
    the default is changed with /set-default instead.
    """
    template = await get_own_template(db, current_user.id, template_id)
    render_or_400(payload.subject, payload.content, sample_context(current_user))

    template.name = payload.name
    template.subject = payload.subject
    template.content = payload.content
    await db.commit()
    await db.refresh(template)
    return template



@router.delete("/{template_id}")
async def delete_email_template(
    template_id : int, 
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    Deletes one of the user's templates. The default template can't be 
    deleted: the user picks another default first, so there is always 
    one to send with.
    """
    template = await get_own_template(db, current_user.id, template_id)

    if template.is_default: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "This is your default template. Make another template the default before deleting it.",
        )

    await db.delete(template)
    await db.commit()
    return {"message": "Template deleted."}

    