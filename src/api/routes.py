"""API route handlers for social media post generation.

This module defines all API endpoints for creating, retrieving,
and managing social media posts.
"""

import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.repositories import EvaluationRepository, PostContentRepository, PostRepository
from src.evaluation.runner import EvaluationRunner
from src.images.storage import ImageStorage

# Create API router
router = APIRouter()


# Request/Response models
class GeneratePostRequest(BaseModel):
    """Request model for generating a post."""

    topic: str = Field(min_length=1, description="Topic to generate posts about")


class GeneratePostResponse(BaseModel):
    """Response model after initiating post generation."""

    post_id: int
    status: str
    message: str


class PostResponse(BaseModel):
    """Response model for post details."""

    post_id: int
    topic: str
    status: str
    image_url: str | None
    linkedin_post: dict | None
    instagram_post: dict | None
    wordpress_post: dict | None
    created_at: str


class ApprovePostResponse(BaseModel):
    """Response model for post approval."""

    post_id: int
    status: str
    message: str


class RejectPostRequest(BaseModel):
    """Request model for rejecting a post."""

    feedback: str


class EditPostRequest(BaseModel):
    """Request model for editing platform content."""

    platform: str
    content: str


class EvaluatePostResponse(BaseModel):
    """Response model for evaluation initiation."""

    post_id: int
    status: str
    message: str


class EvaluationResult(BaseModel):
    """Model for individual evaluation result."""

    metric_name: str
    score: float
    evaluator_type: str
    created_at: str


class GetEvaluationsResponse(BaseModel):
    """Response model for getting post evaluations."""

    post_id: int
    evaluations: list[EvaluationResult]


# Route handlers
@router.post("/posts/generate", response_model=GeneratePostResponse)
async def generate_post(
    request: GeneratePostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate social media posts for a topic.

    This endpoint initiates the post generation workflow in the background.
    The agent will generate content for LinkedIn, Instagram, and WordPress,
    then wait for human review.

    Args:
        request: Topic to generate posts about
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Post ID and status
    """
    from src.agent.graph import workflow
    from src.agent.state import PostGenerationState
    from src.db.database import SessionLocal

    # Create post record
    post_repo = PostRepository(db)
    post = post_repo.create(topic=request.topic, status="generating")
    post_id = post.id

    # Background task to run the agent workflow
    async def run_workflow():
        """Run the agent workflow in background."""
        db_session = SessionLocal()
        try:
            # Create initial state
            initial_state = PostGenerationState(
                topic=request.topic,
                post_id=post_id,
            )

            # Run workflow until it hits the interrupt (wait_for_approval)
            config = {"configurable": {"thread_id": f"post_{post_id}"}}
            await workflow.ainvoke(initial_state.model_dump(), config=config)

        except Exception as e:
            # Update post status to error
            post_repo_bg = PostRepository(db_session)
            post_repo_bg.update_status(post_id, "error")
            print(f"Error in workflow for post {post_id}: {e}")
        finally:
            db_session.close()

    # Add background task
    background_tasks.add_task(run_workflow)

    return GeneratePostResponse(
        post_id=post_id,
        status="generating",
        message="Post generation started. The agent will generate content and wait for your review.",
    )


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post_by_id(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get a post by ID with all generated content.

    Args:
        post_id: Post database ID
        db: Database session

    Returns:
        Post details with all platform content

    Raises:
        HTTPException: If post not found
    """
    # Get post from database
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Get all platform content
    content_repo = PostContentRepository(db)
    all_content = content_repo.get_by_post_id(post_id)

    # Parse content by platform
    linkedin_post = None
    instagram_post = None
    wordpress_post = None

    for content in all_content:
        try:
            parsed_content = json.loads(content.content)
            if content.platform == "linkedin":
                linkedin_post = parsed_content
            elif content.platform == "instagram":
                instagram_post = parsed_content
            elif content.platform == "wordpress":
                wordpress_post = parsed_content
        except json.JSONDecodeError:
            # If content is not valid JSON, skip it
            pass

    return PostResponse(
        post_id=post.id,
        topic=post.topic,
        status=post.status,
        image_url=post.image_url,
        linkedin_post=linkedin_post,
        instagram_post=instagram_post,
        wordpress_post=wordpress_post,
        created_at=post.created_at.isoformat(),
    )


@router.get("/posts", response_model=list[PostResponse])
async def list_posts(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all posts with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status: Optional status filter
        db: Database session

    Returns:
        List of posts
    """
    # Get posts from database
    post_repo = PostRepository(db)
    posts = post_repo.get_all(skip=skip, limit=limit, status=status)

    # Get content for all posts
    content_repo = PostContentRepository(db)

    results = []
    for post in posts:
        # Get all platform content for this post
        all_content = content_repo.get_by_post_id(post.id)

        # Parse content by platform
        linkedin_post = None
        instagram_post = None
        wordpress_post = None

        for content in all_content:
            try:
                parsed_content = json.loads(content.content)
                if content.platform == "linkedin":
                    linkedin_post = parsed_content
                elif content.platform == "instagram":
                    instagram_post = parsed_content
                elif content.platform == "wordpress":
                    wordpress_post = parsed_content
            except json.JSONDecodeError:
                pass

        results.append(
            PostResponse(
                post_id=post.id,
                topic=post.topic,
                status=post.status,
                image_url=post.image_url,
                linkedin_post=linkedin_post,
                instagram_post=instagram_post,
                wordpress_post=wordpress_post,
                created_at=post.created_at.isoformat(),
            )
        )

    return results


@router.post("/posts/{post_id}/approve", response_model=ApprovePostResponse)
async def approve_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Approve all generated content for a post.

    This resumes the agent workflow and finalizes the post.

    Args:
        post_id: Post database ID
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Approval confirmation

    Raises:
        HTTPException: If post not found or not in review state
    """
    from src.agent.graph import workflow
    from src.db.database import SessionLocal

    # Verify post exists and is in review state
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    if post.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail=f"Post {post_id} is not in review state (current status: {post.status})",
        )

    # Background task to resume workflow with approval
    async def resume_with_approval():
        """Resume workflow with approval."""
        db_session = SessionLocal()
        try:
            # Update state with approval
            config = {"configurable": {"thread_id": f"post_{post_id}"}}

            # Get current state and update approval_status
            current_state = await workflow.aget_state(config)
            if current_state and current_state.values:
                updated_state = current_state.values.copy()
                updated_state["approval_status"] = "approved"

                # Resume workflow from the interrupt
                await workflow.ainvoke(updated_state, config=config)

        except Exception as e:
            post_repo_bg = PostRepository(db_session)
            post_repo_bg.update_status(post_id, "error")
            print(f"Error resuming workflow for post {post_id}: {e}")
        finally:
            db_session.close()

    # Add background task
    background_tasks.add_task(resume_with_approval)

    # Update post status
    post_repo.update_status(post_id, "finalizing")

    return ApprovePostResponse(
        post_id=post_id,
        status="approved",
        message="Post approved. Finalizing content...",
    )


@router.post("/posts/{post_id}/reject")
async def reject_post(
    post_id: int,
    request: RejectPostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Reject generated content and provide feedback for regeneration.

    The agent will use the feedback to regenerate improved content.

    Args:
        post_id: Post database ID
        request: Rejection feedback
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Rejection confirmation

    Raises:
        HTTPException: If post not found or not in review state
    """
    from src.agent.graph import workflow
    from src.db.database import SessionLocal

    # Verify post exists and is in review state
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    if post.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail=f"Post {post_id} is not in review state (current status: {post.status})",
        )

    # Background task to resume workflow with rejection
    async def resume_with_rejection():
        """Resume workflow with rejection and feedback."""
        db_session = SessionLocal()
        try:
            # Update state with rejection and feedback
            config = {"configurable": {"thread_id": f"post_{post_id}"}}

            # Get current state and update with rejection
            current_state = await workflow.aget_state(config)
            if current_state and current_state.values:
                updated_state = current_state.values.copy()
                updated_state["approval_status"] = "rejected"
                updated_state["feedback"] = request.feedback

                # Resume workflow - will go to apply_feedback node
                await workflow.ainvoke(updated_state, config=config)

        except Exception as e:
            post_repo_bg = PostRepository(db_session)
            post_repo_bg.update_status(post_id, "error")
            print(f"Error resuming workflow for post {post_id}: {e}")
        finally:
            db_session.close()

    # Add background task
    background_tasks.add_task(resume_with_rejection)

    # Update post status
    post_repo.update_status(post_id, "regenerating")

    return {
        "post_id": post_id,
        "status": "rejected",
        "message": "Post rejected. Regenerating content based on your feedback...",
    }


@router.post("/posts/{post_id}/edit")
async def edit_post_content(
    post_id: int,
    request: EditPostRequest,
    db: Session = Depends(get_db),
):
    """Edit content for a specific platform.

    Args:
        post_id: Post database ID
        request: Platform and new content
        db: Database session

    Returns:
        Edit confirmation

    Raises:
        HTTPException: If post not found
    """
    # Verify post exists
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Validate platform
    valid_platforms = ["linkedin", "instagram", "wordpress"]
    if request.platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}",
        )

    # Update or create content for the platform
    content_repo = PostContentRepository(db)
    existing_content = content_repo.get_by_post_and_platform(post_id, request.platform)

    if existing_content:
        # Update existing content
        content_repo.update_content(post_id, request.platform, request.content)
    else:
        # Create new content
        content_repo.create(post_id, request.platform, request.content)

    return {
        "post_id": post_id,
        "platform": request.platform,
        "status": "updated",
        "message": f"{request.platform.capitalize()} content has been updated",
    }


@router.post("/evaluate/{post_id}", response_model=EvaluatePostResponse, status_code=202)
async def evaluate_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger evaluation for a post.

    Runs all evaluators on the generated content.

    Args:
        post_id: Post database ID
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Evaluation initiation confirmation

    Raises:
        HTTPException: If post not found
    """
    from src.db.database import SessionLocal

    # Verify post exists
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Run evaluation in background
    async def run_evaluation():
        """Background task to run evaluation."""
        # Create a new database session for the background task
        db_session = SessionLocal()
        try:
            runner = EvaluationRunner()
            await runner.evaluate_post(post_id, db_session)
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error evaluating post {post_id}: {e}")
        finally:
            db_session.close()

    background_tasks.add_task(run_evaluation)

    return EvaluatePostResponse(
        post_id=post_id,
        status="evaluation_started",
        message="Evaluation has been queued and will run in the background",
    )


@router.get("/posts/{post_id}/evaluations", response_model=GetEvaluationsResponse)
async def get_post_evaluations(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get evaluation results for a post.

    Args:
        post_id: Post database ID
        db: Database session

    Returns:
        List of evaluation metrics and scores

    Raises:
        HTTPException: If post not found
    """
    # Verify post exists
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Get all evaluations for this post
    eval_repo = EvaluationRepository(db)
    evaluations = eval_repo.get_by_post_id(post_id)

    # Convert to response model
    evaluation_results = [
        EvaluationResult(
            metric_name=eval.metric_name,
            score=eval.score,
            evaluator_type=eval.evaluator_type,
            created_at=eval.created_at.isoformat(),
        )
        for eval in evaluations
    ]

    return GetEvaluationsResponse(post_id=post_id, evaluations=evaluation_results)


@router.get("/posts/{post_id}/image")
async def get_post_image(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get the image file for a post.

    Args:
        post_id: Post database ID
        db: Database session

    Returns:
        Image file

    Raises:
        HTTPException: If post or image not found
    """
    # Verify post exists
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Get image path from storage
    image_storage = ImageStorage()
    image_path = image_storage.get_image(post_id)

    if not image_path:
        raise HTTPException(status_code=404, detail=f"Image not found for post {post_id}")

    # Determine media type based on file extension
    path = Path(image_path)
    extension = path.suffix.lower()
    media_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(extension, "image/png")

    return FileResponse(image_path, media_type=media_type)
